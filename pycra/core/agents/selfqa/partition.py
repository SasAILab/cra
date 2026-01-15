#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/1/14 17:30
# @Author  : lizimo@nuist.edu.cn
# @File    : partition.py
# @Description: the subgraph partition algorithm
import random
from collections import deque
from typing import Any, Iterable, List, AsyncIterator

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
    ) -> AsyncIterator[Community]:
        nodes = await g.get_all_nodes()
        edges = await g.get_all_edges()

        adj, _ = self._build_adjacency_list(nodes, edges)

        used_n: set[str] = set()
        used_e: set[frozenset[str]] = set()

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
                    comm_e.append(tuple(sorted(it)))
                    cnt += 1
                    # push nodes that are not visited
                    for n in it:
                        if n not in used_n:
                            queue.append((NODE_UNIT, n))

            if comm_n or comm_e:
                yield Community(id=seed, nodes=comm_n, edges=comm_e)

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
    ) -> AsyncIterator[Community]:
        nodes = await g.get_all_nodes()
        edges = await g.get_all_edges()

        adj, _ = self._build_adjacency_list(nodes, edges)

        used_n: set[str] = set()
        used_e: set[frozenset[str]] = set()

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
                    comm_e.append(tuple(sorted(it)))
                    cnt += 1
                    # push neighboring nodes
                    for n in it:
                        if n not in used_n:
                            stack.append((NODE_UNIT, n))

            if comm_n or comm_e:
                yield Community(id=seed, nodes=comm_n, edges=comm_e)
