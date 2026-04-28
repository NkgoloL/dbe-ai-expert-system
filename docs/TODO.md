# DBE AI Expert System — Master TODO

**Last Updated:** April 29, 2026
**Review Source:** Comprehensive Technical Review Report
**Overall Delivery Status:** ~35% functional | Phase 2 in progress | Phases 3–5 not started

---

## Legend

| Symbol | Meaning |
|--------|---------|
| 🔴 | Critical — blocks functionality or is a security risk |
| 🟠 | High — must be resolved before next phase |
| 🟡 | Medium — important for production readiness |
| 🟢 | Low — quality-of-life / polish |
| ⚡ | Quick win — estimated < 1 day effort |
| 🔒 | Security-related |
| 🧪 | Test-related |
| 🏗️ | Infrastructure / IaC |
| 📄 | Documentation |

---

## 🚨 IMMEDIATE — Fix Before Any Further Development

These are blocking bugs or critical security vulnerabilities that must be resolved before any other work proceeds.

- [ ] 🔴 ⚡ 🔒 **[BUG] Fix Pydantic v2 `BaseSettings` import in `src/orchestration/main.py`**
  - `from pydantic import BaseSettings` throws `ImportError` on Pydantic v2.3.0 (currently pinned)
  - Add `pydantic-settings>=2.0.0` to `requirements.txt` and `pyproject.toml`
  - Update import to `from pydantic_settings import BaseSettings`

- [ ] 🔴 ⚡ 🔒 **[SECURITY] Parameterize all Gremlin queries in `src/ingestion/graph_manager.py`**
  - `add_document_node()` uses f-string interpolation to construct Gremlin queries — query injection risk
  - Replace all f-string query construction with `gremlinpython` bindings dictionary pattern:
    ```python
    # Replace this:
    query = f"g.addV('Document').property('id', '{doc_id}')"
    # With this:
    query = "g.addV('Document').property('id', id_val)"
    self.client.submit(query, {"id_val": doc_id}).all().result()
    ```
  - Audit all methods in `graph_manager.py` for the same pattern

- [ ] 🔴 ⚡ 🧪 **[BUG] Fix `TestKnowledgeGraphSchemaValidation` and `TestSchemaEnforcement` — `setUp()` not called by pytest**
  - These classes use `setUp()` without inheriting from `unittest.TestCase`
  - pytest does not call `setUp()` on plain classes — `self.manager` is never initialized
  - Convert to `@pytest.fixture` injection or add `unittest.TestCase` inheritance

- [ ] 🔴 ⚡ **[BUG] Wire `retrieve_context()` in `src/orchestration/main.py` to the knowledge graph**
  - Current implementation returns a static formatted string — completely disconnected from Cosmos DB
  - This means the `/ask` endpoint never uses any ingested knowledge
  - Implement graph traversal to retrieve relevant document vertices by query keyword match

---

## PHASE 2 — Intelligence & Data (Complete remaining ~50%)

### 2.1 Core Bug Fixes & Code Quality

- [ ] 🟠 ⚡ **Replace f-string log formatting across all modules**
  - Affected files: `pipeline.py`, `graph_manager.py`, `feedback_loop.py`, `lineage_tracker.py`
  - Replace `logger.info(f"Ingesting {doc_path}")` with `logger.info("Ingesting %s", doc_path)`
  - Rationale: f-strings evaluate eagerly regardless of log level — wastes CPU, risks data exposure in stack traces

- [ ] 🟠 ⚡ **Remove deprecated `asyncio.get_event_loop()` usage in `tests/test_models.py`**
  - `loop.run_until_complete()` with `get_event_loop()` is deprecated in Python 3.10+
  - Replace with `asyncio.run()` or add `pytest-asyncio` and use `@pytest.mark.asyncio`

- [ ] 🟡 **Make `KnowledgeGraphManager` initialization lazy / fault-tolerant**
  - Gremlin client is instantiated eagerly in `__init__()` — if Cosmos is unreachable, pod fails to start
  - Implement lazy initialization: create client on first use with retry backoff
  - Add health check method to verify connectivity independently of pod startup

- [ ] 🟡 **Make `initialize_graph()` idempotent in `graph_manager.py`**
  - Repeated calls create duplicate vertices and raise errors in production
  - Use Gremlin `coalesce()` pattern:
    ```python
    "g.V().has('ExpertSystem','id','dbe_root').fold().coalesce(unfold(), addV('ExpertSystem').property('id','dbe_root'))"
    ```

- [ ] 🟡 **Validate category vertex existence before creating edges in `add_document_node()`**
  - Linking to a non-existent category vertex creates orphaned edges
  - Add pre-flight `g.V(category_id).count()` check before the `addE()` call

- [ ] 🟢 **Externalise `get_schema_definition()` to a config file or environment-driven registry**
  - Hardcoded dict in `graph_manager.py` requires code changes to extend the schema
  - Move to `config/graph_schema.json` and load at runtime

### 2.2 Knowledge Graph — Traversal & Reasoning

- [ ] 🟠 **Implement graph traversal methods in `KnowledgeGraphManager`**
  - The graph manager can write nodes/edges but has zero read/query methods — the core reasoning layer is absent
  - Required methods:
    - `get_documents_by_category(category_id)` — retrieve all docs under a category
    - `search_documents_by_keyword(keyword)` — full-text or property scan
    - `get_related_categories(doc_id)` — two-hop traversal
    - `get_agent_triggers(query_type)` — resolve which agent to invoke
  - All methods must use parameterized Gremlin bindings (see security fix above)

- [ ] 🟠 **Connect `retrieve_context()` in orchestration to graph traversal**
  - After implementing traversal methods above, replace the stub:
    ```python
    async def retrieve_context(query: str) -> str:
        # Replace stub with real graph retrieval
        docs = graph_manager.search_documents_by_keyword(query)
        return "\n".join([d["content"] for d in docs])
    ```
  - Inject `KnowledgeGraphManager` as a FastAPI dependency

- [ ] 🟡 **Add edge property support to graph schema**
  - Current edges (`manages`, `contains`, etc.) have no properties
  - Add `confidence`, `timestamp`, and `weight` edge properties for traversal scoring

- [ ] 🟡 **Implement Gremlin connection pooling and WebSocket reconnect strategy**
  - Single `gremlinpython` client with no reconnect — any network blip kills the connection permanently
  - Use tenacity or a custom retry decorator with exponential backoff

### 2.3 Test Coverage — Phase 2

- [ ] 🔴 🧪 **Replace vacuous performance assertions in `TestGraphQueryPerformance`**
  - Current tests only assert `expected_max_latency_ms > 0` — this validates nothing
  - Integrate `PerformanceBenchmark` class from `e2e_flow_helpers.py` to record actual execution time
  - Assert `actual_latency_ms <= threshold_ms` using `time.perf_counter()` around real or mocked calls

- [ ] 🟠 🧪 **Exercise `E2EFlowOrchestrator` in the test suite**
  - `tests/e2e_flow_helpers.py` is never imported or called by any test
  - Add `tests/test_e2e_orchestrator.py` to instantiate and invoke `E2EFlowOrchestrator.ingest_and_link_document()`

- [ ] 🟠 🧪 **Add tests for `AzureMLExpertModel` with mocked `httpx` responses**
  - Only `BaselinePolicyModel` is tested — the Azure ML inference path has zero test coverage
  - Use `pytest-httpx` or `respx` to mock the `httpx.AsyncClient.post()` call for success and error paths

- [ ] 🟠 🧪 **Add tests for `KnowledgeIngestionPipeline.ingest_from_blob()`**
  - Only `upsert_to_cosmos()` is tested; the blob download path is untested
  - Mock `BlobServiceClient` to simulate successful and failed blob downloads

- [ ] 🟠 🧪 **Add Gremlin injection attempt test**
  - Add a test that passes a malicious `doc_name` (e.g., `"test').drop().V('`)
  - Assert the query executes without dropping graph vertices (validates parameterization fix)

- [ ] 🟡 🧪 **Add negative path tests for FastAPI REST API**
  - Missing request body → 422 validation error
  - Empty `query` string → appropriate error or empty response
  - Malformed JSON → 422
  - `rating` out of range (0, 6) → 422

- [ ] 🟡 🧪 **Add test for `FeedbackLoopManager.save_to_feedback_store()` with blob upload**
  - Current feedback tests only check that the `/feedback` endpoint returns 200
  - Mock `BlobServiceClient` to verify blob is uploaded with correct filename and JSON content

- [ ] 🟡 🧪 **Set up Cosmos DB Emulator in GitHub Actions**
  - Use `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator` as a service container
  - Run real Gremlin integration tests against it — removes dependency on live Azure credentials

---

## PHASE 3 — Integration & Scalability

### 3.1 CI/CD Pipeline (Application)

> **Current state:** Only Terraform infrastructure pipeline exists. Zero application automation.

- [ ] 🔴 🏗️ **Add Python unit test step to GitHub Actions workflow**
  - Create `.github/workflows/application.yml` or extend `infrastructure.yml`
  - Steps: `pip install -e ".[dev]"` → `pytest tests/ -v --cov=src --cov-report=xml`
  - Block merge to `main` if tests fail

- [ ] 🔴 🏗️ **Add Docker image build step to CI/CD**
  - Build `Dockerfile` on every push to `develop` and `main`
  - Tag image with git SHA and branch name
  - Validate image starts successfully (`docker run --rm <image> python -c "import src"`)

- [ ] 🔴 🏗️ **Add ACR image push step to CI/CD**
  - Authenticate to ACR using federated identity (OIDC with GitHub Actions)
  - Push to `<acr>.azurecr.io/agent-orchestrator:<sha>` on `main` branch
  - Tag as `latest` only on successful test run

- [ ] 🔴 🏗️ **Add Helm deploy step to CI/CD**
  - After ACR push, run `helm upgrade --install` against the AKS cluster
  - Use kubeconfig stored as GitHub Actions secret
  - Implement blue/green or rolling update strategy

- [ ] 🟠 🏗️ **Add container image security scanning to CI/CD**
  - Integrate Trivy or Grype after Docker build step
  - Fail pipeline on CRITICAL severity CVEs in application or base image

- [ ] 🟠 🏗️ **Add Python SAST scanning (Bandit) to CI/CD**
  - `bandit -r src/ -ll` — fail on high-severity findings
  - Add to application workflow as a required check

- [ ] 🟠 🏗️ **Add Terraform security scanning (Checkov) to CI/CD**
  - `checkov -d infrastructure/` — catch IaC misconfigurations automatically
  - Integrate into the existing `infrastructure.yml` workflow

- [ ] 🟡 🏗️ **Add dependency vulnerability scanning to CI/CD**
  - Use `safety check` or `pip-audit` against `requirements.txt`
  - Block builds with known critical CVEs in direct dependencies

### 3.2 Terraform Infrastructure Gaps

- [ ] 🔴 🏗️ **Add `azurerm_container_registry` resource to `infrastructure/main.tf`**
  - The Helm chart references `<acr-name>.azurecr.io` but no ACR is provisioned
  - Add resource, enable admin access for initial setup, then move to managed identity auth

- [ ] 🔴 🏗️ **Add Cosmos DB Gremlin database and graph resources to Terraform**
  - `azurerm_cosmosdb_account` enables Gremlin but no database or graph container is provisioned
  - Add `azurerm_cosmosdb_gremlin_database` and `azurerm_cosmosdb_gremlin_graph` resources
  - Set partition key to `/category` to match application code

- [ ] 🔴 🏗️ **Add `outputs.tf` to export connection strings and endpoints**
  - CI/CD and application cannot consume provisioned resources without outputs
  - Export: Cosmos endpoint, ACR login server, AKS FQDN, APIM gateway URL, Key Vault URI

- [ ] 🟠 🏗️ **Bind AKS managed identity to Cosmos DB and Storage RBAC roles**
  - AKS `identity` block uses SystemAssigned but no `azurerm_role_assignment` grants it access to Cosmos or Storage
  - Add `Cosmos DB Built-in Data Contributor` and `Storage Blob Data Contributor` role assignments

- [ ] 🟠 🏗️ **Enable `purge_protection_enabled = true` on Key Vault for production workspace**
  - Currently `false` — accidental deletion of secrets is permanent with no recovery
  - Gate this on `var.environment == "prod"` using a conditional

- [ ] 🟠 🏗️ **Add second `geo_location` block to Cosmos DB for high availability**
  - Single region with `enable_automatic_failover = false` — no DR
  - Add a secondary read region with `failover_priority = 1`

- [ ] 🟡 🏗️ **Upgrade APIM SKU from `Developer_1` to `Standard_1` for production**
  - Developer SKU has no SLA and is single-region only
  - Gate on `var.environment` — use Developer for dev, Standard for prod

- [ ] 🟡 🏗️ **Separate Terraform into modules: `networking`, `data`, `compute`, `monitoring`**
  - `main.tf` is a single 200+ line monolith — difficult to maintain and plan selectively
  - Refactor into modules under `infrastructure/modules/`

- [ ] 🟢 🏗️ **Add `terraform.tfvars.example` with non-sensitive variable defaults**
  - New contributors have no reference for required variable values
  - Document expected values for all variables defined in `variables.tf`

### 3.3 Helm Chart Gaps

- [ ] 🔴 🏗️ **Create `helm/dbe-agent-orchestrator/templates/hpa.yaml`**
  - `values.yaml` defines `autoscaling.*` but no HPA manifest exists in `templates/`
  - The autoscaling configuration is silently ignored without this file

- [ ] 🟠 🏗️ **Create `helm/dbe-agent-orchestrator/templates/externalsecret.yaml` or `secretproviderclass.yaml`**
  - Deployment references secrets from Key Vault but no CSI driver manifest is defined
  - Implement `SecretProviderClass` for Azure Key Vault Provider for Secrets Store CSI Driver
  - Remove hard-coded `secretKeyRef` blocks that assume secrets are manually pre-created

- [ ] 🟠 🏗️ **Remove `localhost:3000` from APIM CORS allowed origins before production**
  - `infrastructure/apim/policy.xml` allows `https://localhost:3000` — development origin must not exist in production config
  - Gate via environment variable or separate policy files per environment

- [ ] 🟡 🏗️ **Create `helm/dbe-agent-orchestrator/templates/configmap.yaml`**
  - Non-sensitive env vars (`PORT`, `LOG_LEVEL`, `ENVIRONMENT`) are hardcoded in `values.yaml`
  - Move to a ConfigMap for cleaner separation of config from deployment definition

- [ ] 🟡 🏗️ **Add `helm/dbe-agent-orchestrator/templates/networkpolicy.yaml`**
  - `values.yaml` defines `networkPolicy.enabled: true` and policy types but no manifest exists
  - Create ingress/egress NetworkPolicy rules that restrict traffic to known ports and namespaces

### 3.4 API Gateway & Orchestration

- [ ] 🔴 🔒 **Add OAuth2/JWT bearer authentication middleware to FastAPI application**
  - APIM enforces JWT validation at the gateway but the FastAPI app has no auth
  - If the service is accessed via internal DNS or during development (bypassing APIM), all endpoints are unauthenticated
  - Implement `fastapi-azure-auth` or a custom `Depends()` OAuth2 bearer dependency

- [ ] 🟠 **Replace `{{client-id}}` placeholder in `infrastructure/apim/policy.xml`**
  - The JWT validation policy has a literal `{{client-id}}` that must be replaced with a Key Vault named value reference
  - Implement as a Key Vault Named Value in Terraform: `azurerm_api_management_named_value`

- [ ] 🟠 🏗️ **Deploy APIM configuration via Terraform or ARM templates**
  - `routes.json` and `policy.xml` are static config files — not deployed by any automation
  - Use `azurerm_api_management_api`, `azurerm_api_management_api_operation`, and `azurerm_api_management_api_policy` resources

- [ ] 🟡 **Implement `/version` endpoint in FastAPI**
  - No way to identify which version of the application is running in a live cluster
  - Return git SHA, build timestamp, and environment from a version endpoint

### 3.5 Monitoring & Observability

- [ ] 🟠 **Integrate Application Insights SDK into FastAPI application**
  - `azurerm_application_insights` is provisioned in Terraform but nothing in the application sends telemetry
  - Add `opencensus-ext-azure` or `opentelemetry-azure-monitor-exporter` to `requirements.txt`
  - Instrument `/ask`, `/feedback`, and expert model calls with distributed traces and custom metrics

- [ ] 🟠 **Add structured logging (JSON format) to all modules**
  - Current `logging.basicConfig(level=logging.INFO)` produces unstructured text logs
  - Replace with `python-json-logger` for Log Analytics compatibility
  - Include `request_id`, `user_id`, `duration_ms` in log records

- [ ] 🟡 **Define Azure Monitor alert rules in Terraform**
  - `azurerm_monitor_action_group` is created but no `azurerm_monitor_metric_alert` resources exist
  - Create alerts for: HTTP 5xx rate > 1%, p95 latency > 2s, feedback rating average < 3.0

- [ ] 🟡 **Add custom metrics to Application Insights**
  - Track: query latency per expert model, feedback rating distribution, graph traversal latency, ingestion throughput

- [ ] 🟢 **Populate `azurerm_portal_dashboard` with meaningful tiles**
  - Current dashboard has an empty `parts: []` — it renders as a blank dashboard
  - Add tiles for: request volume, error rate, p95 latency, active pods, Cosmos RU consumption

---

## PHASE 4 — Optimization

### 4.1 Feedback Loop & ML Pipeline

- [ ] 🟡 **Define Azure ML retraining pipeline in YAML or Python SDK**
  - `FeedbackLoopManager.trigger_retraining()` logs a warning and returns `not_configured`
  - Implement a real `azure.ai.ml.entities.Pipeline` with data prep, training, and registration steps
  - Store pipeline definition in `src/optimization/retraining_pipeline.py`

- [ ] 🟡 **Implement feedback threshold logic in `FeedbackLoopManager`**
  - Retraining should trigger after N low-rated feedback items, not after every single low rating
  - Read `FEEDBACK_RETRAINING_THRESHOLD` from environment (defined in `.env.example` but not used)
  - Implement a counter in blob metadata or Cosmos DB before triggering

- [ ] 🟡 **Implement `log_inference_event()` telemetry push in `lineage_tracker.py`**
  - Method body is a stub with a comment: "Extend this method to push custom telemetry"
  - Implement push to Azure Monitor custom events or an Event Hub

- [ ] 🟢 **Implement model promotion gating in the retraining pipeline**
  - New model versions should only be promoted if they outperform the current production model
  - Add evaluation step comparing validation accuracy before `azurerm_machine_learning_model` registration

### 4.2 Performance Tuning

- [ ] 🟡 **Add Redis caching layer for frequently asked queries**
  - The `/ask` endpoint performs graph traversal and ML inference on every request
  - Cache responses keyed on query hash with TTL from `CACHE_TTL_SECONDS` env var (already documented in `.env.example`)
  - Add `redis` or `upstash-redis` to dependencies

- [ ] 🟡 **Implement load testing for `/ask` endpoint**
  - No performance baseline exists for the orchestration service
  - Use `locust` or `k6` to establish p50/p95/p99 latency and throughput limits
  - Define SLO targets before production launch

- [ ] 🟡 **Tune Cosmos DB indexing policy for knowledge graph queries**
  - Default Cosmos indexing policy indexes all fields — unnecessary for Gremlin workloads
  - Define a custom indexing policy in Terraform targeting only queried properties

- [ ] 🟢 **Profile and optimize `KnowledgeIngestionPipeline` for bulk ingestion**
  - Current pipeline processes documents one at a time via `upsert_item()`
  - Implement `execute_item_batch()` for bulk upsert when ingesting multiple documents

### 4.3 Advanced Reasoning

- [ ] 🟡 **Implement LLM integration for advanced query reasoning**
  - The `perform_reasoning()` function in `main.py` returns a static string template
  - Integrate an LLM (Anthropic Claude via API, Azure OpenAI, or local model) to synthesize context + expert advice into a coherent response
  - Implement prompt templates in `src/orchestration/prompts/`

- [ ] 🟡 **Implement chain-of-thought reasoning pattern**
  - Multi-step queries (e.g., "Which schools in Gauteng lack infrastructure AND have policy gaps?") require multi-hop graph traversal combined with LLM reasoning
  - Implement a ReAct or chain-of-thought orchestration loop

- [ ] 🟡 **Add reasoning trace logging for audit trails**
  - Government deployments require explainability — log every reasoning step with inputs, graph nodes consulted, and model used
  - Store traces in Cosmos DB with TTL for compliance retention

---

## PHASE 5 — Production & Governance

### 5.1 Security Hardening

- [ ] 🔴 🔒 **Execute and remediate findings from `scripts/security_audit.ps1`**
  - Run against a real Azure resource group
  - Document and close all `Write-Warning` and `Write-Error` findings

- [ ] 🟠 🔒 **Implement API key and secret rotation procedures**
  - Document rotation runbook for: Cosmos keys, Azure ML keys, JWT secret, Storage keys
  - Automate rotation using Azure Key Vault rotation policies where supported

- [ ] 🟠 🔒 **Add SSL/TLS certificate management automation**
  - Helm values reference `cert-manager.io/cluster-issuer: "letsencrypt-prod"` but cert-manager is not in the infrastructure
  - Add cert-manager Helm chart deployment to CI/CD or Terraform

- [ ] 🟠 🔒 **Implement secrets scanning in CI/CD**
  - Add `trufflesecurity/trufflehog` or `gitleaks` to GitHub Actions to prevent accidental credential commits
  - Run on every PR as a required status check

- [ ] 🟡 🔒 **OWASP Top 10 validation**
  - Validate: injection (covered by Gremlin fix), broken auth (JWT middleware), sensitive data exposure, security misconfiguration
  - Document validation results per OWASP category

- [ ] 🟡 🔒 **Add Content-Security-Policy and HSTS headers to APIM policy**
  - `policy.xml` sets `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`
  - Add `Strict-Transport-Security: max-age=31536000; includeSubDomains` and a CSP header

### 5.2 Compliance

- [ ] 🟠 🔒 **Execute and remediate findings from `scripts/compliance_checks.ps1`**
  - Run against provisioned Azure resources
  - Confirm: blob encryption at rest, HTTPS-only storage, Key Vault diagnostic settings, AKS managed identity

- [ ] 🟡 **Implement audit logging retention policy**
  - Define log retention periods for APIM event hub logs, Application Insights, and Cosmos audit logs
  - Align with applicable frameworks (POPIA, GDPR, government data retention policies)

- [ ] 🟡 **Define and document RBAC roles for all service identities**
  - Document which identity has which role on which Azure resource
  - Principle of least privilege — remove any broad `Contributor` assignments

- [ ] 🟢 📄 **Create compliance artifacts document**
  - Document encryption at rest/transit, access control, audit logging, and data residency for compliance review

### 5.3 Production Launch

- [ ] 🟠 📄 **Write deployment runbook**
  - Step-by-step instructions for deploying to a new environment from scratch
  - Include: Terraform apply order, secret seeding, Cosmos DB graph initialization, smoke test steps

- [ ] 🟠 **Implement smoke test suite for production**
  - Post-deploy verification: health check, `/ask` with a known query and expected keyword in response, feedback submission
  - Run automatically as the final step in the CI/CD deploy pipeline

- [ ] 🟠 **Define SLA and incident response plan**
  - Define RTO/RPO targets for the knowledge graph and orchestration service
  - Document on-call escalation path and runbook for common failure scenarios

- [ ] 🟡 **Create disaster recovery and backup strategy**
  - Cosmos DB continuous backup policy
  - Runbook for restoring graph from a point-in-time backup
  - AKS node pool recovery procedure

- [ ] 🟡 📄 **Write API reference documentation**
  - Enable FastAPI's built-in OpenAPI UI (`/docs`) in non-production environments
  - Export OpenAPI spec and publish to APIM developer portal

- [ ] 🟢 📄 **Write operations onboarding guide**
  - Guide for operations team covering: monitoring dashboards, alert triage, common errors, log query examples

---

## ONGOING / CROSS-CUTTING

### Documentation

- [ ] 🟡 📄 **Update `README.md` with accurate project status**
  - Current README states "Initial Implementation Phase" — update to reflect Phase 2 progress
  - Add architecture diagram render (Mermaid is defined in `docs/architecture.md` but not linked from README)
  - Add prerequisites: Python 3.10+, `pydantic-settings` note, Azure CLI version

- [ ] 🟡 📄 **Document environment variable requirements in `README.md`**
  - `.env.example` is comprehensive but not linked or explained in README
  - Add a "Configuration" section explaining required vs. optional env vars

- [ ] 🟢 📄 **Add docstrings to all public methods missing them**
  - `src/orchestration/main.py`: `retrieve_context()`, `perform_reasoning()`, `get_expert_model()`
  - `src/ingestion/pipeline.py`: class-level docstring

### Code Hygiene

- [ ] 🟡 **Add `pyproject.toml` linting and formatting configuration**
  - Add `[tool.ruff]` or `[tool.flake8]` section to `pyproject.toml`
  - Add `ruff` or `flake8` + `black` to dev dependencies
  - Enforce via CI/CD pre-commit check

- [ ] 🟡 **Add `pytest-cov` minimum coverage threshold enforcement**
  - Add `--cov-fail-under=80` to pytest CI/CD invocation
  - Current untested paths (AzureML inference, blob ingestion, graph traversal) will force test writing

- [ ] 🟡 **Fix `pyproject.toml` package discovery configuration**
  - `[tool.setuptools] package-dir = {"src" = "src"}` is non-standard
  - Should be `package-dir = {"" = "src"}` or use `find:` with proper source layout
  - Current config may cause import resolution issues in some environments

- [ ] 🟢 **Add `.pre-commit-config.yaml`**
  - Hooks: `black` (formatting), `ruff` (linting), `bandit` (security), `gitleaks` (secret scan)
  - Prevents code quality issues from reaching CI

---

## BLOCKERS — Must Resolve Before Phases 3–5 Can Begin

> These are external dependencies and environment prerequisites, not code tasks.

- [ ] 🔴 🏗️ **Provision active Azure subscription with sufficient quota**
  - Required for: Cosmos DB Gremlin, AKS (min 4 vCPUs), APIM Standard, ML Workspace
- [ ] 🔴 🏗️ **Provision Azure Container Registry (ACR)**
  - Required for: Docker image push, Helm chart deployment to AKS
- [ ] 🔴 🏗️ **Configure CI/CD runner identity (GitHub Actions OIDC or Service Principal)**
  - Required for: Terraform apply, ACR push, AKS helm deploy
- [ ] 🔴 🏗️ **Provision Cosmos DB with Gremlin database and graph container**
  - Required for: real integration tests, end-to-end `/ask` flow
- [ ] 🟠 🏗️ **Provision real Azure ML Workspace and create a managed online endpoint**
  - Required for: `AzureMLExpertModel` inference testing, feedback loop retraining

---

## Task Summary

| Category | Total Tasks | Critical/High | Medium | Low |
|----------|------------|--------------|--------|-----|
| Immediate bugs | 4 | 4 | 0 | 0 |
| Phase 2 — Code & Graph | 18 | 9 | 7 | 2 |
| Phase 3 — CI/CD & Infra | 24 | 12 | 9 | 3 |
| Phase 4 — Optimization | 12 | 0 | 9 | 3 |
| Phase 5 — Production | 12 | 4 | 6 | 2 |
| Cross-cutting | 8 | 0 | 6 | 2 |
| Blockers | 5 | 5 | 0 | 0 |
| **TOTAL** | **83** | **34** | **37** | **12** |

---

*Generated from Technical Review Report — April 29, 2026*
*Next review checkpoint: Upon real Cosmos DB integration and CI/CD pipeline activation*
