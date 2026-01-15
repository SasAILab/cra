import re
from abc import ABC, abstractmethod
from typing import Any, Optional

from pycra.core.llm_server import BaseLLMClient
from pycra.utils.logger import selfqa_logger as logger
from pycra.utils.common import compute_content_hash, detect_main_language
from pycra.core.templates.selfqa import AGGREGATED_GENERATION_PROMPT, COT_GENERATION_PROMPT, MULTI_HOP_GENERATION_PROMPT

class BaseGenerator(ABC):
    """
    Generate QAs based on given prompts.
    """

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    @staticmethod
    @abstractmethod
    def build_prompt(
        batch: tuple[list[tuple[str, dict]], list[tuple[Any, Any, dict]]]
    ) -> str:
        """Build prompt for LLM based on the given batch"""

    @staticmethod
    @abstractmethod
    def parse_response(response: str) -> Any:
        """Parse the LLM response and return the generated QAs"""

    async def generate(
        self,
        batch: tuple[
            list[tuple[str, dict]], list[tuple[Any, Any, dict] | tuple[Any, Any, Any]]
        ],
    ) -> dict[str, Any]:
        """
        Generate QAs based on a given batch.
        :param batch
        :return: QA pairs
        """
        result = {}
        prompt = self.build_prompt(batch)
        response = await self.llm_client.generate_answer(prompt)
        qa_pairs = self.parse_response(response)  # generate one or more QA pairs
        result.update(qa_pairs)
        return result

    @staticmethod
    def format_generation_results(
        results: list[dict], output_data_format: str
    ) -> list[dict[str, Any]]:
        if output_data_format == "Alpaca":
            results = [
                {
                    "instruction": v["question"],
                    "input": "",
                    "output": v["answer"],
                }
                for item in results
                for k, v in item.items()
            ]
        elif output_data_format == "Sharegpt":
            results = [
                {
                    "conversations": [
                        {"from": "human", "value": v["question"]},
                        {"from": "gpt", "value": v["answer"]},
                    ]
                }
                for item in results
                for k, v in item.items()
            ]
        elif output_data_format == "ChatML":
            results = [
                {
                    "messages": [
                        {"role": "user", "content": v["question"]},
                        {"role": "assistant", "content": v["answer"]},
                    ]
                }
                for item in results
                for k, v in item.items()
            ]
        else:
            raise ValueError(f"Unknown output data format: {output_data_format}")
        return results


class AggregatedGenerator(BaseGenerator):
    """
    Aggregated Generator follows a TWO-STEP process:
    1. rephrase: Rephrase the input nodes and edges into a coherent text that maintains the original meaning.
                 The rephrased text is considered as answer to be used in the next step.
    2. question generation: Generate relevant questions based on the rephrased text.
    """

    @staticmethod
    def build_prompt(
        batch: tuple[list[tuple[str, dict]], list[tuple[Any, Any, dict]]]
    ) -> str:
        """
        Build prompts for REPHRASE.
        :param batch
        :return:
        """
        nodes, edges = batch
        entities_str = "\n".join(
            [
                f"{index + 1}. {node[0]}: {node[1]['description']}"
                for index, node in enumerate(nodes)
            ]
        )
        relations_str = "\n".join(
            [
                f"{index + 1}. {edge[0]} -- {edge[1]}: {edge[2]['description']}"
                for index, edge in enumerate(edges)
            ]
        )
        language = detect_main_language(entities_str + relations_str)

        # TODO: configure add_context
        #     if add_context:
        #         original_ids = [
        #             node["source_id"].split("<SEP>")[0] for node in _process_nodes
        #         ] + [edge[2]["source_id"].split("<SEP>")[0] for edge in _process_edges]
        #         original_ids = list(set(original_ids))
        #         original_text = await text_chunks_storage.get_by_ids(original_ids)
        #         original_text = "\n".join(
        #             [
        #                 f"{index + 1}. {text['content']}"
        #                 for index, text in enumerate(original_text)
        #             ]
        #         )
        prompt = AGGREGATED_GENERATION_PROMPT[language]["ANSWER_REPHRASING"].format(
            entities=entities_str, relationships=relations_str
        )
        return prompt

    @staticmethod
    def parse_rephrased_text(response: str) -> Optional[str]:
        """
        Parse the rephrased text from the response.
        :param response:
        :return: rephrased text
        """
        rephrased_match = re.search(
            r"<rephrased_text>(.*?)</rephrased_text>", response, re.DOTALL
        )
        if rephrased_match:
            rephrased_text = rephrased_match.group(1).strip()
        else:
            logger.warning("Failed to parse rephrased text from response: %s", response)
            return None
        return rephrased_text.strip('"').strip("'")

    @staticmethod
    def _build_prompt_for_question_generation(answer: str) -> str:
        """
        Build prompts for QUESTION GENERATION.
        :param answer:
        :return:
        """
        language = detect_main_language(answer)
        prompt = AGGREGATED_GENERATION_PROMPT[language]["QUESTION_GENERATION"].format(
            answer=answer
        )
        return prompt

    @staticmethod
    def parse_response(response: str) -> dict:
        question_match = re.search(r"<question>(.*?)</question>", response, re.DOTALL)
        if question_match:
            question = question_match.group(1).strip()
        else:
            logger.warning("Failed to parse question from response: %s", response)
            return {"question": ""}
        return {"question": question.strip('"').strip("'")}

    async def generate(
        self,
        batch: tuple[
            list[tuple[str, dict]], list[tuple[Any, Any, dict] | tuple[Any, Any, Any]]
        ],
    ) -> dict[str, Any]:
        """
        Generate QAs based on a given batch.
        :param batch
        :return: QA pairs
        """
        result = {}
        rephrasing_prompt = self.build_prompt(batch)
        response = await self.llm_client.generate_answer(rephrasing_prompt)
        context = self.parse_rephrased_text(response)
        if not context:
            return result
        question_generation_prompt = self._build_prompt_for_question_generation(context)
        response = await self.llm_client.generate_answer(question_generation_prompt)
        question = self.parse_response(response)["question"]
        if not question:
            return result
        logger.debug("Question: %s", question)
        logger.debug("Answer: %s", context)
        qa_pairs = {
            compute_content_hash(question): {
                "question": question,
                "answer": context,
            }
        }
        result.update(qa_pairs)
        return result


class CoTGenerator(BaseGenerator):
    @staticmethod
    def build_prompt(
        batch: tuple[list[tuple[str, dict]], list[tuple[Any, Any, dict]]]
    ) -> str:
        """
        Build prompts for COT Template Design.
        :param batch:
        :return:
        """
        nodes, edges = batch
        entities_str = "\n".join(
            [
                f"{index + 1}. {node[0]}: {node[1]['description']}"
                for index, node in enumerate(nodes)
            ]
        )
        relationships_str = "\n".join(
            [
                f"{index + 1}. {edge[0]} -- {edge[1]}: {edge[2]['description']}"
                for index, edge in enumerate(edges)
            ]
        )
        language = detect_main_language(entities_str + relationships_str)
        prompt = COT_GENERATION_PROMPT[language]["COT_TEMPLATE_DESIGN"].format(
            entities=entities_str, relationships=relationships_str
        )
        return prompt

    @staticmethod
    def build_prompt_for_cot_generation(
        batch: tuple[list[tuple[str, dict]], list[tuple[Any, Any, dict]]],
        question: str,
        reasoning_path: str,
    ) -> str:
        """
        Build prompts for COT Generation.
        """
        nodes, edges = batch
        entities_str = "\n".join(
            [
                f"{index + 1}. {node[0]}: {node[1]['description']}"
                for index, node in enumerate(nodes)
            ]
        )
        relationships_str = "\n".join(
            [
                f"{index + 1}. {edge[0]} -- {edge[1]}: {edge[2]['description']}"
                for index, edge in enumerate(edges)
            ]
        )
        language = detect_main_language(entities_str + relationships_str)
        prompt = COT_GENERATION_PROMPT[language]["COT_GENERATION"].format(
            entities=entities_str,
            relationships=relationships_str,
            question=question,
            reasoning_template=reasoning_path,
        )
        return prompt

    @staticmethod
    def parse_response(response: str) -> dict:
        """
        Parse CoT template from response.
        :param response:
        :return: dict with question and reasoning_path
        """
        question_match = re.search(r"<question>(.*?)</question>", response, re.DOTALL)
        reasoning_path_match = re.search(
            r"<reasoning_path>(.*?)</reasoning_path>", response, re.DOTALL
        )

        if question_match and reasoning_path_match:
            question = question_match.group(1).strip()
            reasoning_path = reasoning_path_match.group(1).strip()
        else:
            logger.warning("Failed to parse response: %s", response)
            return {}

        question = question.strip('"').strip("'")
        reasoning_path = reasoning_path.strip('"').strip("'")

        logger.debug("CoT Question: %s", question)
        logger.debug("CoT Reasoning Path: %s", reasoning_path)
        return {
            "question": question,
            "reasoning_path": reasoning_path,
        }

    async def generate(
        self,
        batch: tuple[
            list[tuple[str, dict]], list[tuple[Any, Any, dict] | tuple[Any, Any, Any]]
        ],
    ) -> dict[str, Any]:
        """
        Generate QAs based on a given batch.
        :param batch
        :return: QA pairs
        """
        result = {}
        prompt = self.build_prompt(batch)
        response = await self.llm_client.generate_answer(prompt)
        response = self.parse_response(response)
        if not response:
            return result
        question, reasoning_path = response["question"], response["reasoning_path"]
        prompt = self.build_prompt_for_cot_generation(batch, question, reasoning_path)
        cot_answer = await self.llm_client.generate_answer(prompt)
        logger.debug("CoT Answer: %s", cot_answer)
        qa_pairs = {
            compute_content_hash(question): {
                "question": question,
                "answer": cot_answer,
                "reasoning_path": reasoning_path,
            }
        }
        result.update(qa_pairs)
        return result


class MultiHopGenerator(BaseGenerator):
    @staticmethod
    def build_prompt(
        batch: tuple[list[tuple[str, dict]], list[tuple[Any, Any, dict]]]
    ) -> str:
        nodes, edges = batch
        entities_str = "\n".join(
            [
                f"{index + 1}. {node[0]}: {node[1]['description']}"
                for index, node in enumerate(nodes)
            ]
        )

        relationships_str = "\n".join(
            [
                f"{index + 1}. {edge[0]} -- {edge[1]}: {edge[2]['description']}"
                for index, edge in enumerate(edges)
            ]
        )
        language = detect_main_language(entities_str + relationships_str)
        prompt = MULTI_HOP_GENERATION_PROMPT[language].format(
            entities=entities_str, relationships=relationships_str
        )
        return prompt

    @staticmethod
    def parse_response(response: str) -> dict:
        question_match = re.search(r"<question>(.*?)</question>", response, re.DOTALL)
        answer_match = re.search(r"<answer>(.*?)</answer>", response, re.DOTALL)

        if question_match and answer_match:
            question = question_match.group(1).strip()
            answer = answer_match.group(1).strip()
        else:
            logger.warning("Failed to parse response: %s", response)
            return {}

        question = question.strip('"').strip("'")
        answer = answer.strip('"').strip("'")
        logger.debug("Question: %s", question)
        logger.debug("Answer: %s", answer)
        return {
            compute_content_hash(question): {
                "question": question,
                "answer": answer,
            }
        }
