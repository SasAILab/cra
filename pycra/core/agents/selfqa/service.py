#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/1/14 19:45
# @Author  : lizimo@nuist.edu.cn
# @File    : generator.py
# @Description: self-qa 生成器 --> 利用子图，在子图上生成问题-答案
import json
import os
import inspect
import pandas as pd
from typing import Union, Iterable

from pycra import settings
from pycra.utils.run_concurrent import run_concurrent
from pycra.core.llm_server import BaseLLMClient
from pycra.utils.logger import selfqa_logger as logger
from pycra.core.agents.selfqa.generator import AggregatedGenerator, MultiHopGenerator, CoTGenerator
from pycra.core.agents.selfqa.sub_graph import SubGraphBuilder

class GenerateService:
    """
    Generate pending review question-answer pairs based on nodes and edges.
    """
    def __init__(self,llm_pycra: BaseLLMClient = None):
        self.llm_client = llm_pycra
        self.method = settings.agents.selfqa.method
        self.data_format = settings.agents.selfqa.data_format
        self.subgraph_builder = SubGraphBuilder()

        if self.method == "aggregated":
            self.generator = AggregatedGenerator(self.llm_client)
        elif self.method == "multi_hop":
            self.generator = MultiHopGenerator(self.llm_client)
        elif self.method == "cot":
            self.generator = CoTGenerator(self.llm_client)
        else:
            raise ValueError(f"Unsupported generation mode: {settings.agents.selfqa.method}")

    async def build(self, namespace) -> Union[pd.DataFrame, Iterable[pd.DataFrame]]:
        async for batch in self.subgraph_builder(namespace):
            result = await self.run(batch)
            if inspect.isgenerator(result): # Determine if result is a generator
                for r in result:
                    yield r
            else:
                yield result

    async def run(self, batch: pd.DataFrame) -> pd.DataFrame:
        """
        batch: The batch is an AsyncIterable[pd.DataFrame] returned by the subgraph_builder method.
        """
        items = batch.to_dict(orient="records")
        results = await self.generate(items)
        return pd.DataFrame(results)

    async def generate(self, items: list[dict]) -> list[dict]:
        """
        Generate question-answer pairs based on nodes and edges.
        :param items
        :return: QA pairs
        """
        # logger.info("[Generation] mode: %s, batches: %d", self.method, len(items))
        items = [(item["nodes"], item["edges"]) for item in items] # To prevent multiple input parameters from being received by yield
        results = await run_concurrent(
            self.generator.generate,
            items,
            desc="selfqa - generating",
            unit="batch",
        )

        # Filter out empty results
        results = [res for res in results if res] # To prevent multiple input parameters from being received by yield
        results = self.generator.format_generation_results(
            results, output_data_format=self.data_format
        )
        return results

if __name__ == "__main__":
    import asyncio
    from pycra.core.llm_server import LLMFactory
    import os
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'
    async def main():
        llm_pycra = LLMFactory.create_llm_cli()
        servicer = GenerateService(llm_pycra=llm_pycra)

        async for df in servicer.build(
            namespace="graph_17_8563139ac1688cf12ab0406911831724"
        ):
            print(df)

    asyncio.run(main())