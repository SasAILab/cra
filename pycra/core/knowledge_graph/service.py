import re
from typing import Union
from collections import Counter, defaultdict

from pycra import settings
from pycra.core.document_processing import chunk_documents, Chunk
from pycra.core.knowledge_graph.graph_store import BaseGraphStorage, NetworkXStorage, neo4j_importer
from pycra.core.templates.kg import KG_EXTRACTION_PROMPT, KG_SUMMARIZATION_PROMPT
from pycra.utils.common import (
    detect_main_language, pack_history_conversations,
    split_string_by_multi_markers, handle_single_entity_extraction,
    handle_single_relationship_extraction, compute_content_hash,
    time_record
)
from pycra.core.llm_server import BaseLLMClient
from pycra.utils.run_concurrent import run_concurrent
from pycra.core.knowledge_graph.models import *
from pycra.utils.logger import cckg_logger

class KgBuilder:
    """
    Entity and relation extraction module based on LLM.
    Uses structured prompting to extract entities and relationships from contract content.
    """
    
    def __init__(self, llm_pycra: BaseLLMClient = None):
        self.logger = cckg_logger
        self.llm_pycra = llm_pycra
        self.max_loop = settings.kg.max_loop

    # local_perception_recognition
    async def local_perception_recognition(self, chunk: Chunk) -> Tuple[Dict[str, List[dict]], Dict[Tuple[str, str], List[dict]]]:
        """
        Main method to extract entities and relationships from contract content.
        
        Args:
            chunk: Chunk of contract Object
            chunk.content = contract_content: Preprocessed contract content
            chunk.id = contract_id: Optional unique identifier for the contract
            
        Returns:
            Dictionary containing extracted entities, relationships, and metadata
        """
        contract_content = chunk.content
        contract_id = chunk.id
        self.logger.info(f"Starting entity and relation extraction from id=:{contract_id}")
        if not contract_content:
            self.logger.error("No contract content provided for extraction")
            raise ValueError("Contract content must be provided")
        language = detect_main_language(contract_content)
        try:
            # TODO few-shot 的例子 要经典 后续业务数据有badcase的可以人工调整后作为few-shot
            hint_prompt = KG_EXTRACTION_PROMPT[language]["TEMPLATE"].format(
                    **KG_EXTRACTION_PROMPT["FORMAT"], input_text=contract_content,
                    entity_types=ENTITY_LIST, entity_types_des=ENTITY_DES)
            hint_prompt_token_count = self.llm_pycra.tokenizer.count_tokens(hint_prompt)
            self.logger.debug(f"the hint prompt token size: \n {hint_prompt_token_count}")
            # initial glean
            final_result = await self.llm_pycra.generate_answer(hint_prompt)
            self.logger.debug("init result: %s", final_result)

            # iterative refinement
            history = pack_history_conversations(hint_prompt, final_result)
            self.logger.debug(f"the history: \n {history}")
            for loop_idx in range(self.max_loop):
                if_loop_result = await self.llm_pycra.generate_answer(
                text=KG_EXTRACTION_PROMPT[language]["IF_LOOP"], history=history
            )
                if_loop_result = if_loop_result.strip().strip('"').strip("'").lower()
                if if_loop_result != "yes":
                    break

                glean_result = await self.llm_pycra.generate_answer(
                    text=KG_EXTRACTION_PROMPT[language]["CONTINUE"], history=history
                )
                self.logger.debug("Loop %s glean: %s", loop_idx + 1, glean_result)

                history += pack_history_conversations(
                    KG_EXTRACTION_PROMPT[language]["CONTINUE"], glean_result
                )
                final_result += glean_result
            self.logger.debug(f"loop after final_result: \n {final_result}")
            # step 4: parse the final result
            records = split_string_by_multi_markers(
                final_result,
                [
                    KG_EXTRACTION_PROMPT["FORMAT"]["record_delimiter"],
                    KG_EXTRACTION_PROMPT["FORMAT"]["completion_delimiter"],
                ],
            )
            self.logger.debug(f"the records: \n {records}")
            nodes = defaultdict(list)
            edges = defaultdict(list)

            for record in records:
                match = re.search(r"\((.*)\)", record)
                if not match:
                    continue
                inner = match.group(1)

                attributes = split_string_by_multi_markers(
                    inner, [KG_EXTRACTION_PROMPT["FORMAT"]["tuple_delimiter"]]
                )

                entity = await handle_single_entity_extraction(attributes, chunk.id)
                if entity is not None:
                    nodes[entity["entity_name"]].append(entity)
                    continue

                relation = await handle_single_relationship_extraction(attributes, chunk.id)
                if relation is not None:
                    key = (relation["src_id"], relation["tgt_id"])
                    edges[key].append(relation)
            self.logger.debug(f"the nodes: \n {nodes} \n the edges: \n {edges}")
        except Exception as e:
            self.logger.error(f"Entity and relation extraction failed: {e}", exc_info=True)
            raise
        return dict(nodes), dict(edges)

    async def merge_nodes(
        self,
        node_data: tuple[str, List[dict]],
        kg_instance: BaseGraphStorage,
    ) -> None:
        entity_name, node_data = node_data
        entity_types = []
        source_ids = []
        descriptions = []

        node = await kg_instance.get_node(entity_name)
        if node is not None:
            entity_types.append(node["entity_type"])
            source_ids.extend(
                split_string_by_multi_markers(node["source_id"], ["<SEP>"])
            )
            descriptions.append(node["description"])
        entity_type = sorted(
            Counter([dp["entity_type"] for dp in node_data] + entity_types).items(),
            key=lambda x: x[1],
            reverse=True,
        )[0][0]

        description = "<SEP>".join(
            sorted(set([dp["description"] for dp in node_data] + descriptions))
        )
        description = await self._handle_kg_summary(entity_name, description, max_summary_tokens=settings.kg.max_summary_tokens)

        source_id = "<SEP>".join(
            set([dp["source_id"] for dp in node_data] + source_ids)
        )

        node_data = {
            "entity_type": entity_type,
            "description": description,
            "source_id": source_id,
        }
        await kg_instance.upsert_node(entity_name, node_data=node_data)

    async def merge_edges(
        self,
        edges_data: tuple[Tuple[str, str], List[dict]],
        kg_instance: BaseGraphStorage,
    ) -> None:
        (src_id, tgt_id), edge_data = edges_data

        source_ids = []
        descriptions = []

        edge = await kg_instance.get_edge(src_id, tgt_id)
        if edge is not None:
            source_ids.extend(
                split_string_by_multi_markers(edge["source_id"], ["<SEP>"])
            )
            descriptions.append(edge["description"])

        description = "<SEP>".join(
            sorted(set([dp["description"] for dp in edge_data] + descriptions))
        )
        source_id = "<SEP>".join(
            set([dp["source_id"] for dp in edge_data] + source_ids)
        )

        for insert_id in [src_id, tgt_id]:
            if not await kg_instance.has_node(insert_id):
                await kg_instance.upsert_node(
                    insert_id,
                    node_data={
                        "source_id": source_id,
                        "description": description,
                        "entity_type": "UNKNOWN",
                    },
                )

        description = await self._handle_kg_summary(
            f"({src_id}, {tgt_id})", description, max_summary_tokens=settings.kg.max_summary_tokens
        )

        await kg_instance.upsert_edge(
            src_id,
            tgt_id,
            edge_data={"source_id": source_id, "description": description},
        )

    async def _handle_kg_summary(
        self,
        entity_or_relation_name: str,
        description: str,
        max_summary_tokens: int = 200,
    ) -> str:
        """
        Handle knowledge graph summary

        :param entity_or_relation_name
        :param description
        :param max_summary_tokens
        :return summary
        """

        tokenizer_instance = self.llm_pycra.tokenizer
        language = detect_main_language(description)
        if language == "en":
            language = "English"
        else:
            language = "Chinese"
        KG_EXTRACTION_PROMPT["FORMAT"]["language"] = language

        tokens = tokenizer_instance.encode(description)
        if len(tokens) < max_summary_tokens:
            return description

        use_description = tokenizer_instance.decode(tokens[:max_summary_tokens])
        prompt = KG_SUMMARIZATION_PROMPT[language]["TEMPLATE"].format(
            entity_name=entity_or_relation_name,
            description_list=use_description.split("<SEP>"),
            **KG_SUMMARIZATION_PROMPT["FORMAT"],
        )
        new_description = await self.llm_pycra.generate_answer(prompt)
        self.logger.info(
            "Entity or relation %s summary: %s",
            entity_or_relation_name,
            new_description,
        )
        return new_description


    async def _split_chunks(self, md_content: str, contract_id: str) -> List[Chunk]:
        new_docs = {
            compute_content_hash(md_content, prefix="md-"): {
                "content": md_content
            }
        }
        inserting_chunks = await chunk_documents(
            new_docs,
            settings.kg.chunk_size,
            settings.kg.chunk_overlap,
            self.llm_pycra.tokenizer,
            text_id=contract_id
        )
        inserting_chunks = {
            k: v for k, v in inserting_chunks.items()
        }
        chunks = [
            Chunk(id=k, content=v["content"]) for k, v in inserting_chunks.items()
        ]
        return chunks

    @time_record
    async def build_graph(self, md_content: Optional[str] = None, contract_id: Optional[str] = None) -> Tuple[
        list[tuple[str, dict]],
        list[tuple[str, str, dict]],
        str
    ]:
        """
        Extract entities and relationships from contract sections individually,
        then merge the results.
        
        Args:
            md_content: str --> the contract raw content of the ocr
            contract_id: Optional unique identifier for the contract
            
        Returns:
            Dictionary containing merged extracted entities, relationships, and metadata
        """
        self.logger.info(f"Starting extract entity and relation for {contract_id} contract_id")
        """
        # core1: 提取实体和关系的时候 要有全局视角 --> 假设第一章和第二章之间的某个实体之间有关联 这种情况 这个实体-关系-实体就必须被挖掘出来
        
        # core2: 如果合同太大 大几十页甚至几百页的情况 --> 如何挖掘出来所有的实体和关系 保证没有遗漏呢? 另外，LLM上下文溢出怎么处理? 
        
        # core3: 实体模型的定义和关系模型的定义 --> 要不断的根据业务badcase来迭代
        
        # core4: 实体和关系提取的准确性保证 --> loop模块+few shot解决遗漏和准确性的问题
        
        # core5: 速度保证 --> llm后端使用vllm/lmdeploy服务 chunks采用一个线程池 局部强召回的时候把全部chunks并发出去 全局再聚合到一起处理
        """
        # TODO 图的质量保证 --> GraphGen的judge模块 来计算loss
        # TODO 图谱的评估指标, 一个高质量的图谱对后续的任务是非常重要的 -->https://deepwiki.com/open-sciencelab/GraphGen/9.2-knowledge-graph-evaluation || https://deepwiki.com/open-sciencelab/GraphGen/9.3-confidence-calculation-and-metrics#yesno-loss-metrics
        """
        图谱评估指标
            指标	描述	质量指标
            total_nodes	图中的节点总数	图表大小
            total_edges	图中的边总数	图密度
            noise_ratio	孤立节点与总节点数的比率	越低越好（< 0.15）
            largest_cc_ratio	最大连通分量的大小/节点总数	数值越高越好（> 0.90）
            avg_degree	所有节点的平均节点度	应该在 [2.0, 5.0] 范围内 --> 节点的度数是指与该节点直接相连的边的数量
            powerlaw_r2	度分布幂律拟合的 R² 值	数值越高越好（> 0.75） --> 度分布：统计图中不同度数（k）的节点数量分布 --> 幂律分布：很多真实网络（社交网络、互联网等）的度分布遵循 P(k) ∝ k^(-γ) 的规律,即少数节点有很多连接（hub节点）, 多数节点只有少量连接 --> R² 值含义: 衡量度分布符合幂律的程度 R² ∈ [0, 1]，越接近1表示拟合越好
            is_robust	布尔值，指示是否满足所有阈值	通过/失败指示器
        """

        # step1: Chapter divisions for md_content
        init_chunks = await self._split_chunks(md_content, contract_id)
        # step2: Local Extraction --> 局部强召回 这一步的目标是“宁可错杀，不可放过”, 在小范围内，尽可能多地把所有潜在的实体和关系都找出来。
        results = await run_concurrent(
            self.local_perception_recognition,
            init_chunks,
            desc="[2/4]Extracting entities and relationships from chunks",
            unit="chunk",
        )
        namespace_postfix = compute_content_hash(md_content)
        namespace = f"{settings.kg.namespace}_{contract_id}_{namespace_postfix}"
        kg_instance = NetworkXStorage(
            settings.kg.working_dir, namespace=namespace
        )
        # step3: 全局拓扑对齐 --> 将不同文本块中抽取的同一个实体统一成一个全局ID。
        nodes = defaultdict(list)
        edges = defaultdict(list)
        for n, e in results:
            for k, v in n.items():
                nodes[k].extend(v)
            for k, v in e.items():
                edges[tuple(sorted(k))].extend(
                    v)
        await run_concurrent(
            lambda kv: self.merge_nodes(kv, kg_instance=kg_instance),
            list(nodes.items()),
            desc="Inserting entities into storage",
        )
        await run_concurrent(
            lambda kv: self.merge_edges(kv, kg_instance=kg_instance),
            list(edges.items()),
            desc="Inserting relationships into storage",
        )
        g = await kg_instance.get_graph()
        file_name = f"{settings.kg.working_dir}/{namespace}.graphml"
        NetworkXStorage.write_nx_graph(graph=g, file_name=file_name)
        return_nodes = await kg_instance.get_all_nodes()
        return_egdes = await kg_instance.get_all_edges()

        return return_nodes, return_egdes, namespace

if __name__ == "__main__":
    import os

    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'
    from pycra.core.llm_server import LLMFactory
    import asyncio
    llm_pycra = LLMFactory.create_llm_cli()
    builder = KgBuilder(llm_pycra)
    md_content = """填写你的合同文本
    """
    contract_id = "27"
    result = asyncio.run(builder.build_graph(md_content, contract_id))