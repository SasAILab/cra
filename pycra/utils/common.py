#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2026/1/12 18:02
# @Author  : lizimo@nuist.edu.cn
# @File    : common.py
# @Description:
import html
import json
import pandas as pd
import os
import re
from typing import Any, Callable
import time
import asyncio
import functools
from hashlib import md5

def compute_args_hash(*args):
    return md5(str(args).encode()).hexdigest()

def compute_content_hash(content, prefix: str = ""):
    return prefix + md5(content.encode()).hexdigest()

def detect_main_language(text):
    """
    Detect the main language of the text, 'zh' for Chinese, 'en' for English

    :param text:
    :return:
    """
    assert isinstance(text, str)

    def is_chinese_char(char):
        return "\u4e00" <= char <= "\u9fff"

    def is_english_char(char):
        return char.isascii() and char.isalpha()

    text = "".join(char for char in text if char.strip())

    chinese_count = sum(1 for char in text if is_chinese_char(char))
    english_count = sum(1 for char in text if is_english_char(char))

    total = chinese_count + english_count
    if total == 0:
        return "en"

    chinese_ratio = chinese_count / total

    if chinese_ratio >= 0.5:
        return "zh"
    return "en"

def pack_history_conversations(*args: str):
    roles = ["user", "assistant"]
    return [
        {"role": roles[i % 2], "content": content} for i, content in enumerate(args)
    ]

def split_string_by_multi_markers(content: str, markers: list[str]) -> list[str]:
    """Split a string by multiple markers"""
    if not markers:
        return [content]
    results = re.split("|".join(re.escape(marker) for marker in markers), content)
    return [r.strip() for r in results if r.strip()]

def clean_str(input: Any) -> str:
    """Clean an input string by removing HTML escapes, control characters, and other unwanted characters."""
    # If we get non-string input, just give it back
    if not isinstance(input, str):
        return input

    result = html.unescape(input.strip())
    # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", result)

async def handle_single_entity_extraction(
    record_attributes: list[str],
    chunk_key: str,
):
    if len(record_attributes) < 4 or record_attributes[0] != '"entity"':
        return None
    # add this record as a node in the G
    entity_name = clean_str(record_attributes[1].upper())
    if not entity_name.strip():
        return None
    entity_type = clean_str(record_attributes[2].upper())
    entity_description = clean_str(record_attributes[3])
    entity_source_id = chunk_key
    return {
        "entity_name": entity_name,
        "entity_type": entity_type,
        "description": entity_description,
        "source_id": entity_source_id,
    }

async def handle_single_relationship_extraction(
    record_attributes: list[str],
    chunk_key: str,
):
    if len(record_attributes) < 4 or record_attributes[0] != '"relationship"':
        return None
    # add this record as edge
    source = clean_str(record_attributes[1].upper())
    target = clean_str(record_attributes[2].upper())
    edge_description = clean_str(record_attributes[3])

    edge_source_id = chunk_key
    return {
        "src_id": source,
        "tgt_id": target,
        "description": edge_description,
        "source_id": edge_source_id,
    }

def time_record(func: Callable):
    """
    一个可以装饰同步或异步函数的计时器装饰器
    """
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            end = time.perf_counter()
            print(f"函数 {func.__name__} 执行时间: {end - start:.6f} 秒")
            return result
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            print(f"函数 {func.__name__} 执行时间: {end - start:.6f} 秒")
            return result
        return sync_wrapper

def normalize_result(result):
    """
    统一把 result 变成可迭代对象
    """
    if isinstance(result, list):
        return result
    return [result]


def serialize_item(item):
    """
    统一序列化单个 item
    """
    if isinstance(item, pd.DataFrame):
        return item.to_dict(orient="records")
    return item