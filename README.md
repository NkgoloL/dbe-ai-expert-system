# DBE AI Expert System

The **DBE AI Expert System** is an advanced agentic AI platform designed for automated knowledge ingestion, expert reasoning, and orchestration using a robust Azure-based architecture.

## Architecture Overview

The system follows a modular pipeline designed for scalability and high-performance expert analysis:

1.  **Knowledge Ingestion**: Data collection and storage via Azure Blob Storage.
2.  **Knowledge Graph**: Structured data representation using Azure Cosmos DB.
3.  **Expert Models Suite**: Specialized AI models managed through Azure Machine Learning.
4.  **Agentic AI Orchestration**: Intelligent routing and task execution logic.
5.  **API Gateway**: Secure endpoint management via Azure API Management.
6.  **Deployment**: Scalable execution on Azure Kubernetes Service (AKS).
7.  **Feedback Loop**: Continuous improvement using Azure ML Pipelines.

## Getting Started

### Prerequisites
- Azure CLI
- Git
- Docker (for local testing/deployment)
- Kubernetes Tools (kubectl, helm)

```bash
git clone <repository-url>
cd dbe-ai-expert-system
pip install -e .
```

### Run locally
```bash
python src/orchestration/main.py
```

### Run tests
```bash
pytest -q
```

### Run specific test modules
```bash
pytest tests/test_ingestion.py -v          # Ingestion pipeline tests
pytest tests/test_models.py -v             # Expert model tests
pytest tests/test_orchestration.py -v      # API orchestration tests
pytest tests/test_graph_integration.py -v  # Knowledge graph integration tests
```

### Run with coverage
```bash
pytest --cov=src --cov-report=html
```

## Current Status: Initial Implementation Phase
We have initialized the core skeletons and infrastructure definitions for all project epics. The project now includes package metadata, stronger service orchestration, Azure-backed feedback plumbing, agent guidance for future contributors, and comprehensive integration test suites for the knowledge graph layer.

### Epics Progress
- [x] **Epic 1: Foundation** - Terraform base, Key Vault, Identity, CI/CD Workflow.
- [x] **Epic 2: Intelligence** - Cosmos DB, Azure ML Workspace, Ingestion Pipeline skeleton.
- [x] **Epic 3: Orchestration** - AKS Cluster, API Gateway, FastAPI Orchestration service.
- [x] **Epic 4: Optimization** - Feedback loop manager, Azure ML pipeline hooks.
- [x] **Epic 5: Governance** - Azure Monitor, Dashboards, and Action Groups.

## Project Structure
- `src/`: Core source code for orchestration and services.
- `infrastructure/`: Terraform or ARM templates for Azure resources.
- `docs/`: Detailed documentation and architecture diagrams.
- `roadmap.md`: Project milestones and future plans.

## Contributing
Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
