# Academic Project Report Sections
## Course: DevOps (Assignment-Based Learning 1 / ABL 1)
### Project: Smart Canteen Ordering System

---

## Section 1: Introduction

### 1.1 Problem Statement & Background
Campus dining facilities face severe congestion during peak lunch hours (12:00 PM – 2:00 PM), leading to protracted physical queues, order errors, inventory discrepancies, and student delays. Traditional token systems lack concurrency control, resulting in out-of-stock race conditions where students pay for dishes that the kitchen cannot fulfill. Furthermore, lack of real-time visibility into kitchen queues leads to unpredictable wait times and counter overcrowding.

### 1.2 Proposed Solution & Objectives
The **Smart Canteen Ordering System** is a production-engineered micro-project designed to modernize campus dining operations through modular software architecture and automated DevOps practices. Key engineering objectives include:
1. **Automated Order Lifecycle & Concurrency Isolation**: Implement transaction-safe ordering with atomic inventory decrement, slot capacity limits, and dynamic kitchen wait-time calculation.
2. **Role-Based Access Control**: Clean separation of capabilities across Students, Canteen Staff, and Administrators.
3. **Continuous Integration & Automated Quality Gates**: Enforce zero-defect code integration using Flake8 linting and Pytest test suites achieving $\ge 80\%$ test coverage.
4. **Declarative Multi-Stage Containerization**: Minimize production container attack surface using non-root runtime environments and built-in health probes.
5. **Continuous Deployment & Orchestration**: Automate container builds, Docker Hub publishing, and Kubernetes deployments (with rolling update strategies) via a 7-stage Jenkins pipeline.

---

## Section 2: Technical Details & System Architecture

### 2.1 Software Architecture
The application is structured following the **Modular Layered Architecture** with Flask Blueprints:
- **Presentation Layer**: Responsive HTML5, modular CSS, Vanilla JavaScript with LocalStorage cart caching, and asynchronous 5-second AJAX polling for live order updates.
- **Application / Service Layer**:
  - `AuthService`: Handles password hashing (PBKDF2/SHA-256), session tokens, and RBAC enforcement.
  - `MenuService`: Handles category filtering, fuzzy search, and automatic "Sold Out" state management when inventory drops to zero.
  - `OrderService`: Executes atomic transactions with row-level locks, prevents duplicate submissions via idempotency tokens, checks pickup slot constraints, and calculates dynamic kitchen queue times.
  - `ReportService`: Aggregates real-time operational revenue, top-selling items, and generates streamed CSV audit reports.
- **Data Layer**: SQLAlchemy ORM with SQLite (development/testing) and support for PostgreSQL/MySQL via dynamic `DATABASE_URL`.
- **WSGI Production Server**: Gunicorn (Linux containers) and Waitress (Windows environments).

### 2.2 DevOps & CI/CD Pipeline
- **Version Control Strategy**: GitFlow-inspired branching strategy (`main`, `develop`, `feature/*`) simulating collaboration across 4 student team members with 10 tracked GitHub issues and linked Pull Requests.
- **Linting & Testing**: Flake8 static analysis and Pytest suite comprising 27 unit and integration tests yielding **85.22% code coverage**.
- **Containerization**: Dual-stage Dockerfile:
  - Stage 1 (`builder`): Compiles wheel caches.
  - Stage 2 (`runtime`): `python:3.12-slim` executing under non-root system user `appuser` (UID 10001) with native `/health` container probes.
- **Jenkins CI/CD Automation**: Declarative pipeline orchestrating Checkout $\rightarrow$ Virtualenv $\rightarrow$ Linting $\rightarrow$ Pytest/Coverage Gate $\rightarrow$ Docker Build $\rightarrow$ Docker Hub Push $\rightarrow$ Kubernetes Rolling Update.
- **Kubernetes Orchestration**: Deployed to the `smart-canteen` namespace featuring:
  - 2 pod replicas with resource limits (`cpu: 500m`, `memory: 256Mi`)
  - Liveness and Readiness probes configured on `/health`
  - Zero-downtime rolling update strategy (`maxSurge: 1`, `maxUnavailable: 0`)
  - External exposure via NodePort Service on port `30080` and NGINX Ingress on `canteen.local`.

---

## Section 3: Results & Screenshot Capture Checklist

To assemble your final submission PDF or report, capture the following screenshots from the running system:

| Figure # | Target View / Screen | Action / Content to Capture | Significance for Viva |
| :---: | :--- | :--- | :--- |
| **Fig 3.1** | **Menu Browsing & Search** (`/menu`) | View items, category pills ("South Indian", "Meals"), search bar filtering by "Biryani", and stock badges. | Proves functional menu filtering and automatic sold-out badging. |
| **Fig 3.2** | **Shopping Cart** (`/cart`) | Items added with quantity adjusters (+ / -), subtotal calculation, and clear cart button. | Demonstrates client-side state management via LocalStorage. |
| **Fig 3.3** | **Checkout & Slot Selection** (`/checkout`) | Radio buttons showing available pickup slots with remaining capacities and 3 payment methods (Wallet, UPI, Cash). | Proves slot capacity limits and mock payment multi-channel support. |
| **Fig 3.4** | **Live Order Status Tracking** (`/orders/<id>`) | Visual 5-step progress stepper (`Placed` $\rightarrow$ `Accepted` $\rightarrow$ `Preparing` $\rightarrow$ `Ready` $\rightarrow$ `Collected`), queue position badge, and estimated wait time. | Proves 5-second asynchronous AJAX polling and queue estimation. |
| **Fig 3.5** | **Staff Kitchen Dashboard** (`/staff/dashboard`) | Active orders queue with 1-click status transition buttons (`Accept Order`, `Start Preparing`, `Mark Ready`, `Collected`). | Demonstrates kitchen workflow state transitions. |
| **Fig 3.6** | **Staff Stock Management** (`/staff/menu`) | Menu item table with numeric stock inputs and instant Enable/Disable availability toggle buttons. | Proves real-time kitchen inventory controls. |
| **Fig 3.7** | **Admin Sales Analytics** (`/admin/dashboard`) | Summary cards (Total Orders, Total Revenue, Cancelled Count), status breakdowns, and top-selling dishes table. | Demonstrates operational business intelligence. |
| **Fig 3.8** | **CSV Sales Report** | Downloaded `canteen_sales_all_time.csv` opened in Excel or VS Code showing audit logs. | Proves reporting service and data export compliance. |
| **Fig 3.9** | **Flake8 & Pytest Coverage Output** | Terminal screenshot of `pytest tests/ --cov=app` showing **27 passed in ~6s** and **85.22% coverage**. | Directly proves requirement for $\ge 80\%$ test coverage and zero lint errors. |
| **Fig 3.10**| **Docker Multi-stage Build & Run** | Terminal output of `docker build -t smart-canteen:1.0.1 .` and `docker ps` showing non-root user and healthy status. | Proves multi-stage build and non-root container security. |
| **Fig 3.11**| **Jenkins Declarative Pipeline** | Jenkins stage view dashboard showing green checkmarks across all 7 stages and archived test trends. | Proves end-to-end CI/CD automation. |
| **Fig 3.12**| **Kubernetes Cluster Status** | Terminal output of `kubectl get all -n smart-canteen` showing 2 running pods, NodePort service (30080), and rollout status. | Proves Kubernetes deployment and high-availability configuration. |

---

## Section 4: Conclusion & Future Enhancements

### 4.1 Conclusion
The **Smart Canteen Ordering System** successfully bridges full-stack application development with modern DevOps engineering principles. By implementing transaction-isolated order processing, atomic stock decrementing, capacity-constrained pickup slots, and live status polling, the project resolves critical campus logistics challenges. On the infrastructure side, declarative containerization, a 7-stage automated Jenkins pipeline, and self-healing Kubernetes orchestration ensure high availability, zero-downtime updates, and reproducible deployments.

### 4.2 Future Enhancements
1. **Real-time WebSockets / SSE**: Upgrade 5-second polling to Server-Sent Events (SSE) or WebSockets for lower network overhead.
2. **Payment Gateway Integration**: Connect live Razorpay / Stripe sandbox APIs in place of mock payment handlers.
3. **Helm Charts**: Package Kubernetes manifests into a versioned Helm chart for automated multi-environment parameterization.
4. **Prometheus & Grafana Dashboard**: Ingest `/health` metrics and request latency into Prometheus with real-time Grafana dashboards.

---

## Section 5: References

1. **Flask Documentation**: Pallets Projects, *Flask Application Factories and Blueprints*, 2024. [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
2. **SQLAlchemy 2.0**: Bayer, M., *SQLAlchemy Unified Tutorial and Transaction Management*, 2024. [https://docs.sqlalchemy.org/](https://docs.sqlalchemy.org/)
3. **Docker Best Practices**: Docker Inc., *Best practices for writing Dockerfiles and multi-stage builds*, 2024. [https://docs.docker.com/develop/develop-images/dockerfile_best-practices/](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
4. **Kubernetes Documentation**: The Kubernetes Authors, *Deployments, Services, and Health Probes*, 2024. [https://kubernetes.io/docs/concepts/workloads/controllers/deployment/](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
5. **Jenkins Pipeline Syntax**: Jenkins Project, *Declarative Pipeline Syntax and Credentials Management*, 2024. [https://www.jenkins.io/doc/book/pipeline/syntax/](https://www.jenkins.io/doc/book/pipeline/syntax/)
6. **OWASP Foundation**: *Top 10 Web Application Security Risks: Broken Access Control & Identification Failures*, 2021.
