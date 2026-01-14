# CRA- A Multi-Agent Collaborative Contract Reviewer System

<div align="center"> 
![CRA Web App](/docs/images/cra-crm-framework.png)

*An enterprise-grade intelligent contract review system powered by Large Language Models (LLMs) and Agent technology.*
</div>

## Features

CRA is designed to transform the traditional manual contract review process into an intelligent, efficient, and standardized workflow.

*   **Intelligent Contract Review**: Automatically identifies risks (liabilities, termination clauses, indemnities) and compliance issues using AI agents.
*   **Smart Drafting**: Generates contract drafts based on templates and structured inputs with AI assistance.
*   **Optimization & Rewrite**: Provides suggestions for clause improvements and compares risks between versions.
*   **Knowledge Management**: Built-in Knowledge Graph (RAG) to store and retrieve legal regulations, internal policies, and historical cases.
*   **Human-in-the-loop**: Ensures legal experts have the final say while reducing their workload by up to 80%.

## Architecture

The system follows a modern microservices architecture:

*   **Frontend**: Next.js (React) + Tailwind CSS for a responsive and modern UI.
*   **Backend (Business)**: Java Spring Boot services (`cra-user-service`, `cra-contract-service`) handling user management, permissions, and contract workflows.
*   **AI Engine**: Python (FastAPI) powered by LangChain and LangGraph for orchestrating complex review agents.
*   **Orchestration**: Temporal for reliable workflow execution and state management.
*   **Data Storage**:
    *   PostgreSQL (Business data & Vector data with `pgvector`)
    *   Redis (Caching)
    *   Qdrant (Vector Database for RAG)

## 🚀 Deployment

### Prerequisites

*   Docker & Docker Compose
*   NVIDIA GPU (optional, for local LLM inference)

### Quick Start with Docker Compose

1.  Clone the repository:
    ```bash
    git clone https://github.com/Elian/ContractReviewAgent.git
    cd ContractReviewAgent
    ```

2.  Start the services:
    ```bash
    cd deploy/compose
    docker-compose up -d
    ```

### LMDeploy Configuration (Optional)

If you wish to use **LMDeploy** for high-performance local LLM inference, you can add the following service to your `docker-compose.yml`:

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

*Note: Update `LLM_SERVICE_URL` in the `agent-core` or `llm-service` configuration to point to `http://lmdeploy:23333`.*

## 🔮 Future Plans

*   **V2.0**: Advanced contract optimization with semantic comparison and multi-tenant support.
*   **Long-term**: Deep learning optimization for specific legal domains, multi-language support, and open API ecosystem.

## Author

**Elian** and the development team.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Elian/ContractReviewAgent&type=Date)](https://star-history.com/#2Elian/crat&Date)
