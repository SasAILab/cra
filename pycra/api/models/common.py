#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/1/12 15:57
# @Author  : lizimo@nuist.edu.cn
# @File    : pycra/api/models/common.py
# @Description:
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

class ContractGraphRequest(BaseModel):
    """Request model for contract graph construction"""
    contract_text: Optional[str] = None # OCR extract md_context
    contract_id: Optional[str] = None # the contract id 唯一的id