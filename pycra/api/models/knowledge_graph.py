#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/1/12 15:59
# @Author  : lizimo@nuist.edu.cn
# @File    : pycra/api/models/knowledge_graph.py
# @Description:
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel

class BuildReturnModel(BaseModel):
    status: str
    nodes: Optional[List[Tuple[str, Dict]]] = None
    edges: Optional[List[Tuple[str, str, Dict]]] = None
