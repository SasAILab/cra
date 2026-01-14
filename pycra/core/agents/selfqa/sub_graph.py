import pandas as pd
from typing import Iterable

from pycra.utils import setup_logger
from pycra import settings
from pycra.core.llm_server import BaseLLMClient
from pycra.core.knowledge_graph.graph_store import NetworkXStorage
from pycra.core.agents.selfqa.partition import DFSPartitioner, BFSPartitioner

class SubGraphBuilder:
    def __init__(self, llm_pycra: BaseLLMClient):
        self.llm_pycra = llm_pycra
        self.partitioner = DFSPartitioner() if settings.kg.sub_graph_method == "dfs" else BFSPartitioner()
        self.logger = setup_logger(name="pycra-selfqa.SubGraphBuilder")

    def build(self, namespaces) -> Iterable[pd.DataFrame]:
        kg_instance = NetworkXStorage(
            working_dir=settings.kg.working_dir, namespace=namespaces
        )
        communities: Iterable = self.partitioner.partition(
            g=kg_instance
        )
        count = 0
        for community in communities:
            count += 1
            batch = self.partitioner.community2batch(community, g=kg_instance)

            yield pd.DataFrame(
                {
                    "nodes": [batch[0]],
                    "edges": [batch[1]],
                }
            )
        self.logger.info("Total communities partitioned: %d", count)


async def main():
    import os
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'
    from pycra.core.llm_server import LLMFactory
    llm_pycra = LLMFactory.create_llm_cli()  # 如果是异步的，需要 await
    builder = SubGraphBuilder(llm_pycra)
    namespace = "graph_16_8563139ac1688cf12ab0406911831724"
    async_gen = builder(namespace)
    results = []
    for df in async_gen:
        results.append(df)
        print(f"获取到子图 DataFrame，形状: {df.shape}")
        print(f"节点数: {len(df['nodes'].iloc[0])}")
        print(f"边数: {len(df['edges'].iloc[0])}")

    print(f"总共获取 {len(results)} 个子图")
    return results

if __name__ == "__main__":
    # import asyncio
    # results = asyncio.run(main())
    import os
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'
    from pycra.core.llm_server import LLMFactory
    llm_pycra = LLMFactory.create_llm_cli()  # 如果是异步的，需要 await
    builder = SubGraphBuilder(llm_pycra)
    namespace = "graph_16_8563139ac1688cf12ab0406911831724"
    async_gen = builder.build(namespace)
    results = []
    for df in async_gen:
        results.append(df)
        print(f"获取到子图 DataFrame，形状: {df.shape}")
        print(f"节点数: {len(df['nodes'].iloc[0])}")
        print(f"边数: {len(df['edges'].iloc[0])}")

    print(f"总共获取 {len(results)} 个子图")