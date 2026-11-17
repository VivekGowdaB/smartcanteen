# Software Requirements Specification (SRS)
## Smart Canteen Ordering System (ABL 1)

---

## 1. Introduction

### 1.1 Purpose
This document provides the formal Software Requirements Specification (SRS) for the **Smart Canteen Ordering System**, an enterprise-inspired micro-project engineered for a college DevOps assignment. The system streamlines campus food ordering, eliminates physical queues, prevents out-of-stock race conditions, and demonstrates modern DevOps practices including automated testing, containerization, and continuous delivery.

### 1.2 Scope
The product encompasses a responsive web portal and REST API serving three user roles: **Student**, **Canteen Staff**, and **Admin**. It provides digital menu browsing, time-slot pickup coordination, mock multi-channel payments, dynamic kitchen wait-time calculation, real-time order tracking, and administrative sales reporting.

---

## 2. Overall Description

### 2.1 User Roles & Personas
- **Student**: Browses menu by category, filters items, manages cart, selects pickup time slot, pays via mock wallet/UPI/cash, monitors real-time order progress via 5s polling, and reorders meals.
- **Canteen Staff**: Monitors live kitchen order queue, transitions order statuses (`Accepted` $\rightarrow$ `Preparing` $\rightarrow$ `Ready` $\rightarrow$ `Collected`), adjusts stock levels, and toggles item availability.
- **Admin**: Views aggregate sales analytics, daily revenue metrics, top-selling dishes, and exports audit-ready CSV reports.

### 2.2 System Assumptions & Dependencies
- Operating Environment: Modern Web Browser (Chrome, Firefox, Edge, Safari).
- Server: Python 3.11/3.12, Flask 3.x, SQLAlchemy 2.x, Gunicorn WSGI.
- Database: SQLite (default) configurable to PostgreSQL via `DATABASE_URL`.
- Containerization: Linux container runtime (Docker / containerd).

---

## 3. Functional Requirements

| Req ID | Module | Description |
| :--- | :--- | :--- |
| **FR-01** | **Authentication** | Users shall be able to register and log in using email/username and hashed passwords. Session state and role assignment (`student`, `staff`, `admin`) shall be securely managed. |
| **FR-02** | **Role-Based Access**| Role-based access control (RBAC) shall prevent students from accessing staff/admin endpoints and restrict staff from administrative revenue analytics. |
| **FR-03** | **Menu Management** | Students shall be able to browse dishes grouped by category and filter items via search queries. Out-of-stock items shall automatically display a "Sold Out" badge. |
| **FR-04** | **Cart & Slot Limiting**| The system shall permit items to be added to a persistent client cart. During checkout, users must select an active pickup slot. The system shall enforce a strict capacity limit per slot. |
| **FR-05** | **Mock Payments** | Users can pay via Student Wallet (debit balance), Mock UPI (instant verification), or Cash on Pickup (mark payment pending until food collection). |
| **FR-06** | **Atomic Stock Check**| When an order is placed, an atomic database transaction shall lock and verify inventory. If any item is depleted, the transaction rolls back with HTTP 409 Conflict. |
| **FR-07** | **Wait Time Estimation**| The system shall calculate an estimated pickup wait time based on pending kitchen queue items and food prep durations. |
| **FR-08** | **Live Order Polling** | The order status view shall poll the server every 5 seconds, dynamically updating the status stepper (`Placed` $\rightarrow$ `Accepted` $\rightarrow$ `Preparing` $\rightarrow$ `Ready` $\rightarrow$ `Collected`). |
| **FR-09** | **Cancellation Rules** | Students can cancel orders only while status is `Placed` or `Accepted`. Cancellation after food has entered `Preparing` or later shall be rejected. Cancelled wallet orders must auto-refund balance and restore inventory. |
| **FR-10** | **Sales Reporting** | Admin can view daily orders, gross revenue, status breakdowns, and download comprehensive sales logs as a CSV file. |

---

## 4. Non-Functional Requirements

- **NFR-01 (Performance)**: Typical HTTP API response times shall be $<500\text{ ms}$ under standard loads.
- **NFR-02 (Reliability & Testing)**: The codebase must maintain $\ge 80\%$ test coverage verified through automated `pytest` and `pytest-cov`.
- **NFR-03 (Security)**: Passwords must be hashed using PBKDF2/SHA-256 before persistence. Form submissions must prevent CSRF and duplicate submissions via unique idempotency tokens.
- **NFR-04 (Observability)**: Dedicated `/health` probe endpoint returning JSON status (`healthy`, `degraded`) for Docker and Kubernetes liveness/readiness probes.
- **NFR-05 (Portability)**: The entire stack must run identically in local development, inside multi-stage Docker containers, and on Kubernetes clusters (Minikube / Docker Desktop / Cloud).
- **NFR-06 (Maintainability)**: Clean modular architecture using Flask Blueprints and separation of concerns (Models, Services, Routes, Templates).
