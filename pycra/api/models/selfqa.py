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


class SelfQaSubgrapnResponse(BaseModel):
    answer: str
