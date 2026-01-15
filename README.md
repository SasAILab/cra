# CRA- A Multi-Agent Collaborative Contract Reviewer System
<div align="center">
  
![Java](https://img.shields.io/badge/Java-17-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![React](https://img.shields.io/badge/React-18-red.svg)
![lmdeploy](https://img.shields.io/badge/lmdeploy-0.11.1-orange.svg)
![Version](https://img.shields.io/badge/version-0.0.1-brightgreen.svg)
[![open issues](https://img.shields.io/github/issues-raw/2Elian/cra)](https://github.com/2Elian/cra/issues)

[![简体中文](https://img.shields.io/badge/简体中文-blue?style=for-the-badge&logo=book&logoColor=white)](./README_CN.md) 
[![English](https://img.shields.io/badge/English-orange?style=for-the-badge&logo=language&logoColor=white)](./README.md)

**An enterprise-grade intelligent contract review system powered by Large Language Models (LLMs) and Agent technology.**
</div>

<p align="center">
  <img src="./docs/images/cra-crm-framework.png" alt="CRA Web应用界面" width="800"/>
</p>

---

## Features

CRA is designed to transform the traditional manual contract review process into an intelligent, efficient, and standardized workflow.

*   **Intelligent Contract Review**: Automatically identifies risks (liabilities, termination clauses, indemnities) and compliance issues using AI agents.
*   **Smart Drafting**: Generates contract drafts based on templates and structured inputs with AI assistance.
*   **Optimization & Rewrite**: Provides suggestions for clause improvements and compares risks between versions.
*   **Knowledge Management**: Built-in Knowledge Graph (RAG) to store and retrieve legal regulations, internal policies, and historical cases.
*   **Human-in-the-loop**: Ensures legal experts have the final say while reducing their workload by up to 80%.

## Architecture

The system follows a modern microservices architecture:

*   **Frontend**: Next.js (React) + Tailwind CSS.
*   **Backend (Business)**: Java Spring Boot services (`cra-user-service`, `cra-contract-service`) handling user management, permissions, and contract workflows.
* **AI Engine:** Python (FastAPI), agent orchestration based on LangChain and LangGraph, knowledge base retrieval based on GraphRAG/LightRAG/ROGRAG. Other modules are based on GraphGen and self-developed technologies.

* **Data Storage:**

  * PostgreSQL (business data)

  * MongoDB (contract data)

  * Elasticsearch (basic search engine)

  * Redis (caching)

  * Qdrant (RAG vector database)

  * neo4j (graph database)

## 🚀 Deployment

### Quick Start with Docker Compose

1.  Clone the repository:
    ```bash
    git clone https://github.com/2Elian/cra.git
    cd cra
    ```

2.  Start the services:
    ```bash
    cd deploy/compose
    docker-compose up -d
    ```

## 🔮 Future Plans

*   **V2.0**: Advanced contract optimization with semantic comparison and multi-tenant support.
*   **Long-term**: Deep learning optimization for specific legal domains, multi-language support, and open API ecosystem.

## Author
![GitHub contributors](https://img.shields.io/github/contributors/2Elian/cra)

**pycra** is independently developed by Elian, an AI algorithm engineer. His research interests lie in post-training of LLM-RL and agent development.


## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=2Elian/cra&type=Date&theme=radical)](https://star-history.com/#2Elian/cra&Date)