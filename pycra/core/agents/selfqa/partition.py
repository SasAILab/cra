#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/1/14 17:30
# @Author  : lizimo@nuist.edu.cn
# @File    : partition.py
# @Description: the subgraph partition algorithm
import random
from collections import deque
from dataclasses import dataclass
from typing import Any, Iterable, List, AsyncIterator, Dict, Set, Tuple
import igraph as ig
from collections import defaultdict
from leidenalg import ModularityVertexPartition, find_partition

from pycra.core.agents.base import BasePartitioner, Community
from pycra.core.knowledge_graph.graph_store import BaseGraphStorage

NODE_UNIT: str = "n"
EDGE_UNIT: str = "e"
"""
how to chose algorithm for bfs and dfs
选择广度优先搜索 (BFS) 的情况：
    你想要的是简单、平衡的社区。
    当地邻里关系至关重要
    你需要可预测、快速的分区
选择 DFS 的情况：
    你的知识图谱具有链式/序列结构
    你想深入探究推理路径。
    您正在处理时间图或因果图。
"""
class BFSPartitioner(BasePartitioner):
    """
    BFS partitioner that partitions the graph into communities of a fixed size.
    1. Randomly choose a unit.
    2. Expand the community using BFS until the max unit size is reached.
    (A unit is a node or an edge.)
    """

    async def partition(
        self,
        g: BaseGraphStorage,
        max_units_per_community: int = 1,
        **kwargs: Any,
    ) -> List[Community]:
        nodes = await g.get_all_nodes()
        edges = await g.get_all_edges()

        adj, _ = self._build_adjacency_list(nodes, edges)

        used_n: set[str] = set()
        used_e: set[frozenset[str]] = set()
        communities: List[Community] = []

        units = [(NODE_UNIT, n[0]) for n in nodes] + [
            (EDGE_UNIT, frozenset((u, v))) for u, v, _ in edges
        ]
        random.shuffle(units)

        for kind, seed in units:
            if (kind == NODE_UNIT and seed in used_n) or (
                kind == EDGE_UNIT and seed in used_e
            ):
                continue

            comm_n: List[str] = []
            comm_e: List[tuple[str, str]] = []
            queue: deque[tuple[str, Any]] = deque([(kind, seed)])
            cnt = 0

            while queue and cnt < max_units_per_community:
                k, it = queue.popleft()
                if k == NODE_UNIT:
                    if it in used_n:
                        continue
                    used_n.add(it)
                    comm_n.append(it)
                    cnt += 1
                    for nei in adj[it]:
                        e_key = frozenset((it, nei))
                        if e_key not in used_e:
                            queue.append((EDGE_UNIT, e_key))
                else:
                    if it in used_e:
                        continue
                    used_e.add(it)

                    u, v = it
                    comm_e.append((u, v))
                    cnt += 1
                    # push nodes that are not visited
                    for n in it:
                        if n not in used_n:
                            queue.append((NODE_UNIT, n))

            if comm_n or comm_e:
                communities.append(
                    Community(id=len(communities), nodes=comm_n, edges=comm_e)
                )

        return communities

class DFSPartitioner(BasePartitioner):
    """
    DFS partitioner that partitions the graph into communities of a fixed size.
    1. Randomly choose a unit.
    2. Random walk using DFS until the community reaches the max unit size.
    (In GraphGen, a unit is defined as a node or an edge.)
    """

    async def partition(
        self,
        g: BaseGraphStorage,
        max_units_per_community: int = 1,
        **kwargs: Any,
    ) -> List[Community]:
        nodes = await g.get_all_nodes()
        edges = await g.get_all_edges()

        adj, _ = self._build_adjacency_list(nodes, edges)

        used_n: set[str] = set()
        used_e: set[frozenset[str]] = set()
        communities: List[Community] = []

        units = [(NODE_UNIT, n[0]) for n in nodes] + [
            (EDGE_UNIT, frozenset((u, v))) for u, v, _ in edges
        ]
        random.shuffle(units)

        for kind, seed in units:
            if (kind == NODE_UNIT and seed in used_n) or (
                kind == EDGE_UNIT and seed in used_e
            ):
                continue

            comm_n, comm_e = [], []
            stack = [(kind, seed)]
            cnt = 0

            while stack and cnt < max_units_per_community:
                k, it = stack.pop()
                if k == NODE_UNIT:
                    if it in used_n:
                        continue
                    used_n.add(it)
                    comm_n.append(it)
                    cnt += 1
                    for nei in adj[it]:
                        e_key = frozenset((it, nei))
                        if e_key not in used_e:
                            stack.append((EDGE_UNIT, e_key))
                            break
                else:
                    if it in used_e:
                        continue
                    used_e.add(it)
                    comm_e.append(tuple(it))
                    cnt += 1
                    # push neighboring nodes
                    for n in it:
                        if n not in used_n:
                            stack.append((NODE_UNIT, n))

            if comm_n or comm_e:
                communities.append(
                    Community(id=len(communities), nodes=comm_n, edges=comm_e)
                )

        return communities

class LeidenPartitioner(BasePartitioner):
    """
    Leiden partitioner that partitions the graph into communities using the Leiden algorithm.
    """

    async def partition(
        self,
        g: BaseGraphStorage,
        max_size: int = 20,
        use_lcc: bool = False,
        random_seed: int = 42,
        **kwargs: Any,
    ) -> List[Community]:
        """
        Leiden Partition follows these steps:
        1. export the graph from graph storage
        2. use the leiden algorithm to detect communities, get {node: community_id}
        3. split large communities if max_size is given
        4. convert {node: community_id} to List[Community]
        :param g
        :param max_size: maximum size of each community, if None or <=0, no limit
        :param use_lcc: whether to use the largest connected component only
        :param random_seed
        :param kwargs: other parameters for the leiden algorithm
        :return:
        """
        nodes = await g.get_all_nodes()  # List[Tuple[str, dict]]
        edges = await g.get_all_edges()  # List[Tuple[str, str, dict]]

        node2cid: Dict[str, int] = await self._run_leiden(
            nodes, edges, use_lcc, random_seed
        )

        if max_size is not None and max_size > 0:
            node2cid = await self._split_communities(node2cid, max_size)

        cid2nodes: Dict[int, List[str]] = defaultdict(list)
        for n, cid in node2cid.items():
            cid2nodes[cid].append(n)

        communities: List[Community] = []
        for cid, nodes in cid2nodes.items():
            node_set: Set[str] = set(nodes)
            comm_edges: List[Tuple[str, str]] = [
                (u, v) for u, v, _ in edges if u in node_set and v in node_set
            ]
            communities.append(Community(id=cid, nodes=nodes, edges=comm_edges))
        return communities

    @staticmethod
    async def _run_leiden(
        nodes: List[Tuple[str, dict]],
        edges: List[Tuple[str, str, dict]],
        use_lcc: bool = False,
        random_seed: int = 42,
    ) -> Dict[str, int]:
        # build igraph
        ig_graph = ig.Graph.TupleList(((u, v) for u, v, _ in edges), directed=False)

        # remove isolated nodes
        ig_graph.delete_vertices(ig_graph.vs.select(_degree_eq=0))

        node2cid: Dict[str, int] = {}
        if use_lcc:
            lcc = ig_graph.components().giant()
            partition = find_partition(lcc, ModularityVertexPartition, seed=random_seed)
            for part_id, cluster in enumerate(partition):
                for v in cluster:
                    node2cid[lcc.vs[v]["name"]] = part_id
        else:
            offset = 0
            for component in ig_graph.components():
                subgraph = ig_graph.induced_subgraph(component)
                partition = find_partition(
                    subgraph, ModularityVertexPartition, seed=random_seed
                )
                for part_id, cluster in enumerate(partition):
                    for v in cluster:
                        original_node = subgraph.vs[v]["name"]
                        node2cid[original_node] = part_id + offset
                offset += len(partition)
        return node2cid

    @staticmethod
    async def _split_communities(
        node2cid: Dict[str, int], max_size: int
    ) -> Dict[str, int]:
        """
        Split communities larger than max_size into smaller sub-communities.
        """
        cid2nodes: Dict[int, List[str]] = defaultdict(list)
        for n, cid in node2cid.items():
            cid2nodes[cid].append(n)

        new_mapping: Dict[str, int] = {}
        new_cid = 0
        for nodes in cid2nodes.values():
            if len(nodes) <= max_size:
                for n in nodes:
                    new_mapping[n] = new_cid
                new_cid += 1
            else:
                for start in range(0, len(nodes), max_size):
                    chunk = nodes[start : start + max_size]
                    for n in chunk:
                        new_mapping[n] = new_cid
                    new_cid += 1
        return new_mapping



if __name__ == "__main__":
    # leiden algorithm test
    import asyncio
    from pycra import settings
    from pycra.core.knowledge_graph.graph_store import NetworkXStorage
    kg_instance = NetworkXStorage(
        working_dir=settings.kg.working_dir, namespace="graph_17_8563139ac1688cf12ab0406911831724"
    )
    partitioner = LeidenPartitioner()
    async def main():
        communities = await partitioner.partition(g=kg_instance)
        return communities
    results = asyncio.run(main())