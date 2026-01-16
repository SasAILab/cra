import asyncio
from typing import Tuple, List, Any, Union, TypeAlias

from pycra.utils.logger import selfqa_logger
from pycra import settings
from pycra.core.agents.base import Community
from pycra.core.knowledge_graph.graph_store import NetworkXStorage
from pycra.core.agents.selfqa.partition import DFSPartitioner, BFSPartitioner, LeidenPartitioner

ComplexType: TypeAlias = list[
    tuple[
        list[tuple[str, dict]],
        list[Union[
            tuple[Any, Any, dict],
            tuple[Any, Any, Any]
        ]]
    ]
]


class SubGraphBuilder:
    def __init__(self):
        self.partitioner = DFSPartitioner() if settings.kg.sub_graph_method == "dfs" else BFSPartitioner()
        if settings.kg.sub_graph_method == "bfs":
            self.partitioner = BFSPartitioner()
        elif settings.kg.sub_graph_method == "dfs":
            self.partitioner = DFSPartitioner()
        self.partitioner_leiden = LeidenPartitioner()
        self.logger = selfqa_logger

    async def __call__(self, namespaces) -> Tuple[ComplexType, ComplexType]:
        kg_instance = NetworkXStorage(
            working_dir=settings.kg.working_dir, namespace=namespaces
        )
        communities_task = self.partitioner.partition(g=kg_instance)
        communities_leiden_task = self.partitioner_leiden.partition(g=kg_instance)
        communities, communities_leiden = await asyncio.gather(
            communities_task,
            communities_leiden_task
        )
        batches_task = self.partitioner.community2batch(communities, g=kg_instance)
        batches_leiden_task = self.partitioner_leiden.community2batch(communities_leiden, g=kg_instance)
        batches, batches_leiden = await asyncio.gather(
            batches_task,
            batches_leiden_task
        )
        self.logger.info(f"Return {settings.kg.sub_graph_method} method Communities count: {len(communities)}")
        self.logger.info(f"Return Leiden method Communities count: {len(communities_leiden)}")
        return batches, batches_leiden
