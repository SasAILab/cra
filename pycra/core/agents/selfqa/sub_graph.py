import pandas as pd
from typing import Iterable, AsyncIterable

from pycra.utils.logger import selfqa_logger
from pycra import settings
from pycra.core.knowledge_graph.graph_store import NetworkXStorage
from pycra.core.agents.selfqa.partition import DFSPartitioner, BFSPartitioner

class SubGraphBuilder:
    def __init__(self):
        self.partitioner = DFSPartitioner() if settings.kg.sub_graph_method == "dfs" else BFSPartitioner()
        self.logger = selfqa_logger

    async def __call__(self, namespaces) -> AsyncIterable[pd.DataFrame]:
        kg_instance = NetworkXStorage(
            working_dir=settings.kg.working_dir, namespace=namespaces
        )
        communities = self.partitioner.partition(g=kg_instance)

        count = 0
        async for community in communities:  # 使用 async for 迭代异步生成器
            count += 1
            batch = await self.partitioner.community2batch(community, g=kg_instance)

            yield pd.DataFrame(
                {
                    "nodes": [batch[0]],
                    "edges": [batch[1]],
                }
            )
        self.logger.info("Total communities partitioned: %d", count)


if __name__ == "__main__":
    import asyncio
    import os
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'
    async def main():
        builder = SubGraphBuilder()
        namespace = "graph_16_8563139ac1688cf12ab0406911831724"
        results = []
        async for df in builder(namespace):  # 使用 async for
            results.append(df)
            print(f"获取到子图 DataFrame，形状: {df.shape}")
            print(f"节点数: {len(df['nodes'].iloc[0])}")
            print(f"边数: {len(df['edges'].iloc[0])}")

        print(f"总共获取 {len(results)} 个子图")
        return results


    # 运行异步主函数
    results = asyncio.run(main())