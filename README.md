# Smart Canteen Ordering System (ABL 1)

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-black.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/Tests-27%20Passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/Coverage-85.22%25-green.svg)]()
[![Flake8](https://img.shields.io/badge/Linter-Flake8%20Passed-blueviolet.svg)]()
[![Docker](https://img.shields.io/badge/Docker-Multi--stage-2496ED.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-NodePort%2030080-326CE5.svg)](https://kubernetes.io/)

A complete, production-grade micro-project engineered for a college **DevOps Assignment-Based Learning (ABL 1)**. The system models a high-throughput campus food ordering portal with atomic inventory decrementing, capacity-constrained pickup slots, live 5-second order polling, role-based access control (Student, Staff, Admin), automated test quality gates, declarative multi-stage containerization, a 7-stage Jenkins CI/CD pipeline, and self-healing Kubernetes deployment.

---

## 🚀 Key Features

- **Role-Based Access Control (RBAC)**: Secure separation between **Student**, **Canteen Staff**, and **Admin** with PBKDF2/SHA-256 password hashing and session tokens.
- **Dynamic Menu & Real-Time Stock Tracking**: Live search, category filtering, and automatic "Sold Out" badging when inventory hits zero.
- **Cart & Capacity-Constrained Pickup Slots**: Client-side cart caching with strict order limits per 30-minute pickup window to prevent kitchen congestion.
- **Mock Multi-Channel Payments**: Instant Student Wallet debit, mock UPI QR simulation, and Cash on Pickup.
- **Order Lifecycle & Dynamic Queue Wait-Time**:
  $$\text{Placed} \longrightarrow \text{Accepted} \longrightarrow \text{Preparing} \longrightarrow \text{Ready} \longrightarrow \text{Collected}$$
  Estimated pickup wait times dynamically calculated based on pending kitchen queue depth.
- **Live Order Polling**: Asynchronous 5-second AJAX polling with an animated progress stepper and kitchen queue position indicator.
- **Edge Case Protection**:
  - Rejection of empty carts.
  - Concurrency-safe atomic stock decrementing (prevents out-of-stock race conditions).
  - Slot capacity overflow protection.
  - Idempotency key protection against rapid duplicate form submissions.
  - Cancellation restriction (strictly rejected once order status reaches `Preparing` or later).
  - Instant wallet refund and inventory restoration on valid cancellations.
- **Staff Kitchen Dashboard**: Real-time incoming queue management and instant inventory adjustments.
- **Admin Analytics & CSV Audit Export**: Daily revenue totals, order status distributions, top-selling dishes, and 1-click CSV download.
- **Observability Probe**: High-speed JSON `/health` endpoint for Docker and Kubernetes probes.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11/3.12, Flask 3.0.3, SQLAlchemy 2.0.30
- **Database**: SQLite (default, zero configuration) / PostgreSQL support via `DATABASE_URL`
- **Frontend**: Responsive CSS (custom modern theme), Vanilla JavaScript (Fetch API, LocalStorage), Jinja2 templates
- **WSGI Production Server**: Gunicorn (Linux containers), Waitress (Windows local)
- **Quality Assurance**: `pytest` 8.2.2, `pytest-cov` 5.0.0, `flake8` 7.1.0
- **DevOps**: Multi-stage `Dockerfile` (non-root `appuser:10001`), declarative `Jenkinsfile` (7 stages), Kubernetes manifests (`k8s/`), and free-tier cloud fallback instructions (Render / Railway).

---

## 📁 Repository Structure

```plaintext
spmabl/
├── .github/                      # GitHub issue and PR templates
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
├── app/                          # Core Flask Application
│   ├── config.py                 # Development, Testing, Production configurations
│   ├── extensions.py             # SQLAlchemy instance initialization
│   ├── models/                   # User, Menu, Order, and Slot models
│   ├── routes/                   # Blueprints: auth, student, staff, admin, api
│   ├── services/                 # Business logic: auth, menu, order transactions, reports
│   ├── static/                   # Custom CSS, client-side Cart & live polling JS
│   └── templates/                # Responsive Jinja2 templates (auth, student, staff, admin)
├── tests/                        # Automated Pytest Suite (27 test cases, 85.22% coverage)
├── docs/                         # Comprehensive Academic & DevOps Documentation
│   ├── SRS.md                    # Software Requirements Specification
│   ├── SDS.md                    # Software Design Specification & REST API Catalog
│   ├── UML.md                    # Mermaid & PlantUML diagrams (Use Case, Class, Sequence, Activity, Deployment)
│   ├── AI_USAGE_LOG.md           # Responsible AI usage ledger
│   ├── DEVOPS_GUIDE.md           # Local, Docker, Jenkins, and Kubernetes execution guide
│   ├── git_workflow.md           # 4-member Git simulation script & Jenkins trigger guide
│   └── REPORT_SECTIONS.md        # Report-ready submission sections with screenshot checklist
├── k8s/                          # Kubernetes Manifests
│   ├── namespace.yaml            # smart-canteen namespace
│   ├── configmap.yaml            # Non-sensitive configuration
│   ├── secret.yaml               # Secret key and DB connection
│   ├── deployment.yaml           # 2 replicas, health probes, non-root user, resource limits
│   ├── service.yaml              # NodePort service on port 30080
│   └── ingress.yaml              # NGINX Ingress configuration
├── Dockerfile                    # Multi-stage build with non-root user and HEALTHCHECK
├── .dockerignore
├── Jenkinsfile                   # Declarative CI/CD pipeline (7 stages + artifacts)
├── requirements.txt              # Application dependencies
├── seed.py                       # Database seeder with sample accounts and dishes
├── wsgi.py                       # WSGI production server entrypoint
└── README.md
```

---

## ⚡ Quick Start (Local Run)

### 1. Setup Environment & Install Dependencies
```powershell
# Navigate to directory
cd spmabl

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1    # On Linux/macOS: source venv/bin/activate

# Install dependencies
python -m pip install -r requirements.txt
```

### 2. Seed Database
```powershell
python seed.py
```

### 3. Run Development Server
```powershell
python wsgi.py
```
Open **`http://localhost:5000`** in your browser.

---

## 🧪 Testing & Linting

Run automated linting and the test suite:
```powershell
# 1. Flake8 Linting (max line length 120)
python -m flake8 app tests --max-line-length=120

# 2. Pytest with Coverage Gate (Target >= 80%)
python -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Results**:
- **Tests Passed**: 27 / 27 (100%)
- **Test Coverage**: **85.22%** (Exceeds required $\ge 80\%$)
- **Flake8 Errors**: 0

---

## 🐳 Docker Containerization

```powershell
# Build multi-stage image tagged with version and build number
docker build -t smart-canteen:1.0.1 -t smart-canteen:latest .

# Run containerized application
docker run -d -p 5000:5000 --name smart-canteen-app smart-canteen:1.0.1

# Verify container health
curl http://localhost:5000/health
```

---

## ☸️ Kubernetes Deployment

```bash
# Apply all manifests to Kubernetes cluster
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Verify deployment rollout
kubectl rollout status deployment/smart-canteen-deployment -n smart-canteen
```
Access via NodePort at `http://<CLUSTER_IP>:30080`.

---

## ☁️ Deploy to Render

1. Push the repository to GitHub, then select **New + → Blueprint** in Render and connect it.
2. Render uses [`render.yaml`](render.yaml) to build the Python service and run Gunicorn on its assigned port. A production `SECRET_KEY` is generated automatically.
3. Before Gunicorn starts, Render seeds demo users and menu items only if the database is completely empty. This step does not reset or overwrite an existing database.

Render's default SQLite filesystem is ephemeral. For persistent data, connect a Render PostgreSQL database and set `DATABASE_URL` to its internal connection URL. Do not configure `PORT` yourself.
The seeded demo admin login is `admin` / `Admin@123`; use demo credentials only for evaluation, not for real users or sensitive data.

---

## 👥 Demo Credentials for Viva Evaluation

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `Admin@123` | Access to sales analytics and CSV export |
| **Staff** | `staff` | `Staff@123` | Access to kitchen order queue and stock manager |
| **Student** | `student1` | `Student@123` | Seeded with ₹500.00 mock wallet balance |
| **Student** | `student2` | `Student@123` | Seeded with ₹350.00 mock wallet balance |

---

## 📖 Complete Documentation Index

- 📋 [Software Requirements Specification (SRS)](docs/SRS.md)
- 📐 [Software Design Specification & REST API (SDS)](docs/SDS.md)
- 📊 [UML Diagrams (Mermaid & PlantUML)](docs/UML.md)
- 🤖 [Responsible AI Usage Ledger](docs/AI_USAGE_LOG.md)
- 🛠️ [DevOps Implementation & Cloud Run Guide](docs/DEVOPS_GUIDE.md)
- 🌿 [4-Member Git Team Workflow Simulation](docs/git_workflow.md)
- 📝 [Academic Project Report Sections](docs/REPORT_SECTIONS.md)
