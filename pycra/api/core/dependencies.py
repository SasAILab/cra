#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/1/13 16:41
# @Author  : lizimo@nuist.edu.cn
# @File    : dependencies.py
# @Description: 全局依赖注入
from abc import ABC, abstractmethod
from typing import Optional, Union

from pycra import settings
from pycra.core.llm_server import LLMFactory
from pycra.core.knowledge_graph.graph_store import neo4j_importer
from pycra.core.knowledge_graph import KgBuilder

class PyCraFactory(ABC):

    @abstractmethod
    def create_current_contract_graphBuild_workflow(self) -> KgBuilder:
        raise NotImplementedError

class ProductionWorkflowFactory(PyCraFactory):
    def __init__(self):
        self.llm_langChain = LLMFactory.create_llm()
        self.llm_pycra = LLMFactory.create_llm_cli()
        self.neo_4j: neo4j_importer
        # embedding model
        # milvus db

    # 如果有异步的self需要传递给后续的router 在这里添加
    async def initialize(self):
        # self.llm_langChain = await LLMFactory.create_llm()
        # self.llm_pycra = await LLMFactory.create_llm_cli()
        pass

    def create_current_contract_graphBuild_workflow(self) -> KgBuilder:
        return KgBuilder(self.llm_pycra)

_factory: Optional[PyCraFactory] = None

async def get_factory() -> ProductionWorkflowFactory:
    global _factory
    if _factory is None:
        _factory = ProductionWorkflowFactory()
        await _factory.initialize()
    return _factory

async def get_kgBuilder_async() -> KgBuilder:
    factory = await get_factory()
    return factory.create_current_contract_graphBuild_workflow()