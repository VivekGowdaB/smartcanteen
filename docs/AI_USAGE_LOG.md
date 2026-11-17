# AI Usage & Responsible Engineering Log
## Smart Canteen Ordering System (ABL 1)

This ledger documents the responsible and transparent use of AI assistance during the engineering, containerization, and automated testing of the Smart Canteen Ordering System.

---

## AI Interaction & Validation Ledger

| Date / Phase | Task & Prompt Objective | AI Generated Code / Artifact | Engineer Validation & Critical Fixes Applied |
| :--- | :--- | :--- | :--- |
| **Phase 1: Architecture** | Initial architectural plan, schema modeling, edge case catalog, and tech stack selection. | `implementation_plan.md` artifact outlining blueprints, ER models, testing strategy, and DevOps pipeline. | Validated all functional requirements against college assignment criteria. Confirmed RBAC roles (Student, Staff, Admin) and transaction-level stock checking strategy. |
| **Phase 2: App Core & Models** | Scaffolding Flask application factory, SQLAlchemy models, and service layer with transaction safety. | `app/config.py`, `app/models/`, `app/services/auth_service.py`, `app/services/order_service.py`. | **Fixed Deprecation**: Replaced deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)`.<br>**Fixed Concurrency**: Enforced atomic row locking and explicit database rollbacks upon stock depletion. |
| **Phase 3: Routes & Frontend** | Blueprints (`auth`, `student`, `staff`, `admin`, `api`), responsive CSS, vanilla JS cart, and live order polling. | Route handlers in `app/routes/`, `style.css`, `cart.js`, and Jinja templates. | **Fixed Jinja Dict Bug**: Identified that `order.to_dict().items` collided with Python's built-in `dict.items` method during JSON serialization in templates. Corrected to `order.to_dict()['items']|tojson`. |
| **Phase 4: Testing & Seeder** | Database seeder (`seed.py`) with test credentials; comprehensive Pytest test suite with coverage $\ge 80\%$. | `seed.py`, `tests/conftest.py`, and 27 test cases covering health, auth, menu, order lifecycle, edge cases, and staff/admin. | **Fixed Windows Console Encoding**: Resolved `UnicodeEncodeError` on Windows CP1252 consoles by adding `sys.stdout.reconfigure(encoding='utf-8')` and ASCII fallbacks.<br>**Fixed Slot Capacity**: Updated `OrderService.place_order` to query database `PickupSlotConfig` dynamically.<br>**Coverage Reached**: Achieved **85.22%** overall test coverage. |
| **Phase 5: DevOps & CI/CD** | Multi-stage Dockerfile and declarative Jenkinsfile with 7 stages and coverage gates. | `Dockerfile`, `.dockerignore`, `Jenkinsfile`. | **Security Hardening**: Enforced non-root user `appuser` (UID 10001) in runtime container stage.<br>**Pipeline Integrity**: Added Flake8 linting and Pytest JUnit/Coverage archiving to Jenkins post actions. |
| **Phase 6: Kubernetes Manifests** | Kubernetes manifests (`k8s/`) for namespace, deployment, service, configmap, secret, and ingress. | `namespace.yaml`, `configmap.yaml`, `secret.yaml`, `deployment.yaml`, `service.yaml`, `ingress.yaml`. | Verified liveness/readiness probes point to `/health`. Configured rolling updates with 2 replicas, zero downtime (`maxSurge: 1`, `maxUnavailable: 0`), and resource limits. |
| **Phase 7: Git Team Simulation** | Simulating a 4-member collaborative Git workflow with 10 issues, conventional commits, and PR descriptions. | `docs/git_workflow.md` with executable PowerShell simulation script. | Structured distinct responsibilities for 4 student members (DevOps, Security, Core Business Logic, Frontend/QA). Added webhook and Poll-SCM trigger setup instructions. |
| **Phase 8: Documentation** | Comprehensive academic documentation: SRS, SDS, UML diagrams, DevOps guide, and viva report sections. | `docs/SRS.md`, `docs/SDS.md`, `docs/UML.md`, `docs/DEVOPS_GUIDE.md`, `docs/REPORT_SECTIONS.md`. | Verified all Mermaid diagrams compile correctly and technical descriptions match the implemented codebase line-for-line. |

---

## Statement of Academic Integrity & Responsible AI Use
AI was utilized as a pair-programming collaborator for code generation, architectural drafting, and test synthesis. All generated code was compiled, linted via `flake8`, executed in an isolated local virtual environment, and rigorously evaluated against 27 automated integration tests with 85.22% coverage. Discrepancies and platform-specific bugs were diagnosed and corrected manually by the engineering team.
