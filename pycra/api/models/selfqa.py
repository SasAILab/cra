#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/1/14 23:10
# @Author  : lizimo@nuist.edu.cn
# @File    : selfqa.py
# @Description:
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel

class SelfQaRequest(BaseModel):
    namespace: str


class SubgraphSummary(BaseModel):
    """子图摘要信息"""
    subgraph_id: int
    node_count: int
    edge_count: int
    nodes_sample: List[str]  # 节点示例
    edges_sample: List[str]  # 边示例

class SelfQaSubgrapnResponse(BaseModel):
    """SELF-QA 子图生成响应"""
    success: bool
    message: str
    total_subgraphs: int
    total_nodes: int
    total_edges: int
    avg_nodes_per_subgraph: float
    avg_edges_per_subgraph: float
    subgraph_summaries: Optional[List[SubgraphSummary]] = None

class selfQaResponse(BaseModel):
    status: str
    data: List[Dict[str, Any]]
