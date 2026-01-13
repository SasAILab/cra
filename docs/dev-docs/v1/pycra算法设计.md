# pycra算法开发文档

## 1. how to build a knowledge graph for your contract

The first step in the pycra framework is to build a knowledge graph for the contract under review, providing data support for subsequent tasks.

### 1.1 why build kg?

- Contracts awaiting review
如果合同不构造成图谱，那么处理方式有2种。第一种方式是直接把合同文本内容作为上下文给到LLM，让LLM分析其中条款的合规性，这种方式的弊端就是可能出现LLM上下文溢出、LLM忽略了某些细节的问题出现。第二种方式是将合同划分成若干个chunks，像传统RAG一样进行处理，而这种方式会出现上下文截断、需预先定义的提问等问题。

合同数据本身具有高度关联性。一个条款中某个词项的价值可能会影响后续条款中可能出现的值。所以，这里构造一张知识图谱作为后续任务的坚实的数据基础是非常有必要的。
Contract data is inherently highly interconnected. The value of a term in one clause may influence the values that may appear in subsequent clauses.

- 后续合同合规审查角度
多跳推理的Agent进行合同的自我审查、无需人工干预
配合GraphRAG进行多跳问题(条款合规性)的问答，实现graph-graph的问答Agent。

### 1.2 how to build?

- step1: Extracting Relevant Entity and Relations from  Contracts of md formate.

这里的核心问题有3个：
```bash
# 跨章节、跨距离的全局一致性与关系发现（Global Consistency & Long-range Relation Mining）
提取实体和关系的时候 要有全局视角 --> 假设第一章和第二章之间的某个实体之间有关联 这种情况 这个实体-关系-实体就必须被挖掘出来 --> 采用局部强召回+全局拓扑对齐可以解决

# 提取实体和关系的时候 要有全局视角 --> 假设第一章和第二章之间的某个实体之间有关联 这种情况 这个实体-关系-实体就必须被挖掘出来
如果合同太大 大几十页甚至几百页的情况 --> 如何挖掘出来所有的实体和关系 保证没有遗漏呢? 另外，LLM上下文溢出怎么处理?  --> 采用局部强召回+全局拓扑对齐可以解决

# 实体模型的定义和关系模型的定义 --> 要不断的根据业务badcase来迭代
```
