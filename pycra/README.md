# pycra: python-contract-review-agent

<div align="center"> 
这里将放我们的cra的算法架构图
</div>

# 核心技术
##  LangGraph


## Agent Skills

**Agent Skills（智能体技能）**是一种将专业知识、指令、脚本和资源打包成模块化“技能包”的机制，让通用 AI 智能体（Agent）能按需加载和使用，变得更专业、高效地执行特定复杂任务，就像给 AI 安装了“专业 App”或“入职手册”一样。它通过**渐进式披露（Progressive Disclosure）**技术，只加载最少信息启动，需要时再加载完整内容，优化了上下文窗口利用，解决了通用 Agent 处理专精任务效率低下的问题。

---

### Agent Skills 的核心概念

- **可组合性 (Composability)**: 将领域知识拆分成独立技能，可以组合使用，构建复杂工作流。  
- **模块化 (Modularity)**: 每个 Skill 是一个包含 `SKILL.md`、脚本、资源（文件）的文件夹，易于分享和复用。  
- **按需加载 (On-Demand Loading)**: AI 只在需要时加载相关技能，提高速度和专注度。  
- **渐进式披露 (Progressive Disclosure)**: 先加载元数据（名称、描述），确认需要再加载完整指令和资源，节省 token。  
- **专业化 (Specialization)**: 将通用 Agent 转变为特定领域的专家，如代码审查、数据分析。  

---

### 举例说明

- **通用 AI（没有技能）**: 无法很好地完成特定任务。  
- **添加代码审查 Skill**: AI 能自动按照团队规范审查代码。  
- **添加数据分析 Skill**: AI 能根据文件类型自动分析数据。  
- **添加报告生成 Skill**: AI 能自动按照模板生成报告。  

---

### 解决了什么问题

- **效率低**: 传统方法需每次在 Prompt 中塞入冗长指导，耗费大量 Token。  
- **知识固化难**: 难以将复杂流程嵌入通用模型。  
- **可复用性差**: 定制化 Agent 分散，不易管理。