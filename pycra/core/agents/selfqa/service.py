#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/1/14 19:45
# @Author  : lizimo@nuist.edu.cn
# @File    : generator.py
# @Description: self-qa 生成器 --> 利用子图，在子图上生成问题-答案
import asyncio
from typing import Any, List, Tuple, Dict

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
        self.generator_aggregated = AggregatedGenerator(self.llm_client)
        self.generator_multihop = MultiHopGenerator(self.llm_client)
        self.generator_cot = CoTGenerator(self.llm_client)

    async def build(self, namespace) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        batches, batches_leiden = await self.subgraph_builder(namespace)
        aggregated_task = run_concurrent(
            self.generator_aggregated.generate,
            batches,
            desc="pycra.selfqa: Generating QAs for aggregated type ",
            unit="batch_aggregated",
        )
        multihop_task = run_concurrent(
            self.generator_multihop.generate,
            batches_leiden,
            desc="pycra.selfqa: Generating QAs for multi_hop type ",
            unit="batch_multi-hop",
        )
        cot_task = run_concurrent(
            self.generator_cot.generate,
            batches_leiden,
            desc="pycra.selfqa: Generating QAs for cot type ",
            unit="batch_cot",
        )
        results, results_multihop, results_cot = await asyncio.gather(
            aggregated_task,
            multihop_task,
            cot_task,
            return_exceptions=True
        )
        results = self.generator_aggregated.format_generation_results(
            results, output_data_format=self.data_format
        )
        results_multihop = self.generator_aggregated.format_generation_results(
            results_multihop, output_data_format=self.data_format
        )
        results_cot = self.generator_aggregated.format_generation_results(
            results_cot, output_data_format=self.data_format
        )
        return results, results_multihop, results_cot