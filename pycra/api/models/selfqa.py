#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/1/14 23:10
# @Author  : lizimo@nuist.edu.cn
# @File    : selfqa.py
# @Description:
from typing import Optional, Dict, Any, List, Tuple, Union
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
    status: str
    batches: list[
    tuple[
        list[tuple[str, dict]],
        list[Union[
            tuple[Any, Any, dict],
            tuple[Any, Any, Any]
        ]]
    ]
]
    batches_leiden: list[
    tuple[
        list[tuple[str, dict]],
        list[Union[
            tuple[Any, Any, dict],
            tuple[Any, Any, Any]
        ]]
    ]
]

class selfQaResponse(BaseModel):
    status: str
    aggregated: List[Dict[str, Any]]
    multi_hop: List[Dict[str, Any]]
    cot: List[Dict[str, Any]]
