# Contract Review Agent (CRA) | 合同审查智能体

基于大语言模型（LLM）和 Agent 技术的企业级智能合同审查系统。

## 功能特征

CRA 旨在将传统的人工合同审查流程转化为智能、高效、标准化的工作流。

*   **智能合同审查**：利用 AI Agent 自动识别合同中的风险点（如责任限制、终止条款、赔偿条款）及合规性问题。
*   **智能起草**：基于预设模板和结构化输入，辅助生成合规的合同草稿。
*   **条款优化与改写**：提供条款修改建议，并对比修改前后的风险变化。
*   **知识管理**：内置知识图谱（RAG），整合法律法规、企业内部政策及历史案例，实现经验复用。
*   **人机协同**：保持人类专家的最终决策权，同时减少 80% 的重复性工作。

## 🏗 技术架构

本系统采用现代化的微服务架构设计：

*   **前端**：Next.js (React) + Tailwind CSS，打造响应式现代 UI。
*   **后端（业务层）**：Java Spring Boot 微服务 (`cra-user-service`, `cra-contract-service`)，处理用户管理、权限及合同流转。
*   **AI 引擎**：Python (FastAPI)，基于 LangChain 和 LangGraph 编排复杂的审查 Agent。
*   **流程编排**：使用 Temporal 保证工作流的可靠执行和状态管理。
*   **数据存储**：
    *   PostgreSQL（业务数据及 `pgvector` 向量数据）
    *   Redis（缓存）
    *   Qdrant（RAG 专用向量数据库）

## 部署指南

### 前置要求

*   Docker & Docker Compose
*   NVIDIA GPU（可选，用于本地 LLM 推理）

### Docker Compose 快速启动

1.  克隆项目代码：
    ```bash
    git clone https://github.com/Elian/ContractReviewAgent.git
    cd ContractReviewAgent
    ```

2.  启动服务：
    ```bash
    cd deploy/compose
    docker-compose up -d
    ```

### LMDeploy 配置指南（可选）

如果您希望使用 **LMDeploy** 进行高性能的本地大模型推理，可以在 `docker-compose.yml` 中添加以下服务配置：

```yaml
  lmdeploy:
    image: openmmlab/lmdeploy:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - ./models:/models
    environment:
      - MODEL_PATH=/models/your-model-weights
    command: lmdeploy serve api_server /models/your-model-weights --server-port 23333 --tp 1
    ports:
      - "23333:23333"
    networks: [cra-net]
```

*注意：启动后，请在 `agent-core` 或 `llm-service` 的配置中，将 `LLM_SERVICE_URL` 指向 `http://lmdeploy:23333`。*

## 🔮 未来计划

*   **V2.0 版本**：引入高级合同优化功能，支持语义级对比及多租户架构。
*   **长期规划**：针对特定法律领域的深度学习优化，支持多语言环境，并构建开放 API 生态。

## 👥 关于作者

**Elian** 及开发团队。

## Star 增长趋势

[![Star History Chart](https://api.star-history.com/svg?repos=Elian/ContractReviewAgent&type=Date)](https://star-history.com/#Elian/ContractReviewAgent&Date)
