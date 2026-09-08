# LLM Usage Metering & Billing Engine

A backend service for tracking API and AI-token usage, enforcing subscription quotas, calculating AI usage costs, and integrating payments.

## Architecture

The system follows a layered architecture that separates HTTP handling, business logic, and data persistence.

```text
                         ┌─────────────────────┐
                         │       Client        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   FastAPI Routers   │
                         │  HTTP / Validation  │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
        ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
        │ Usage / Quota │ │ Pricing /      │ │ Payment /      │
        │ Services       │ │ Budget Services│ │ Webhook Logic  │
        └───────┬────────┘ └────────────────┘ └───────┬────────┘
                │                                      │
                └──────────────────┬───────────────────┘
                                   ▼
                         ┌─────────────────────┐
                         │     SQLAlchemy      │
                         │   Models / ORM      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     PostgreSQL      │
                         │     Persistence     │
                         └─────────────────────┘

        ┌─────────────────────┐
        │   Celery Worker     │
        │ Background Tasks    │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │       Redis         │
        │ Broker / Backend    │
        └─────────────────────┘

        ┌─────────────────────┐
        │      Paystack       │
        │ Payment Provider    │
        └──────────┬──────────┘
                   │
                   ▼
             Webhook Endpoint
```

### Main Components

* **FastAPI** — HTTP API, request validation, and routing.
* **Services** — business logic for usage metering, quotas, pricing, AI budgets, and payments.
* **SQLAlchemy** — ORM and database access layer.
* **PostgreSQL** — persistent storage for tenants, plans, subscriptions, usage events, and payment events.
* **Alembic** — database schema migrations.
* **Celery** — background task processing.
* **Redis** — Celery message broker and result backend.
* **Paystack** — payment initialization, verification, and webhook processing.

### Usage Flow

```text
API Request
    │
    ▼
FastAPI
    │
    ▼
Usage / Generate Service
    │
    ├── Check Idempotency
    ├── Check Quota
    ├── Check AI Budget
    ├── Calculate Cost
    │
    ▼
UsageEvent
    │
    ▼
PostgreSQL
```

Usage events are protected by a tenant-scoped idempotency key so that a retried request does not create duplicate billable usage.

### Payment Flow

```text
Client
  │
  ▼
POST /payments/initialize
  │
  ▼
Paystack
  │
  ▼
Authorization / Payment
  │
  ▼
Paystack Webhook
  │
  ├── Verify Signature
  ├── Check Event Idempotency
  ├── Verify Amount
  │
  ▼
Subscription → Active
```

## Project Structure

```text
app/
├── models/
│   ├── tenant.py
│   ├── plan.py
│   ├── subscription.py
│   ├── usage_event.py
│   └── payment_event.py
│   └── payment.py
│
├── routers/
│   ├── tenant.py
│   ├── plan.py
│   ├── subscription.py
│   ├── usage.py
│   ├── generate.py
│   ├── payment.py
│   └── webhook.py
│
├── schemas/
│   ├── usage.py
│   ├── generate.py
│   └── payment.py
│   └── subscription.py
│   └── tenant.py
│
├── services/
│   ├── usage_service.py
│   ├── quota_service.py
│   ├── pricing_service.py
│   ├── budget_service.py
│   └── paystack_service.py
│   ├── plan_service.py
│   ├── subscription_service.py
│   ├── tenant_service.py
│   ├── token_service.py
│   └── usage_query_service.py
│
├── tasks/
│   └── usage_tasks.py
│
├── celery_app.py
├── database.py
├── dependencies.py
└── main.py

alembic/
scripts/
test/
.env
.env.example
```

## Setup

### 1. Prerequisites

Install:

* Python 3.12+
* PostgreSQL
* Redis

### 2. Create a Virtual Environment

```bash
python3 -m venv virtual
source virtual/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file:

```env
DATABASE_URL=postgresql+psycopg://metering_user:your_password@localhost:5432/metering_billing

PAYSTACK_SECRET_KEY=sk_test_your_key_here
PAYSTACK_INITIALIZE_URL=https://api.paystack.co/transaction/initialize
PAYSTACK_VERIFY_URL=https://api.paystack.co/transaction/verify/

REDIS_URL=redis://localhost:6379/0
```

Do not commit `.env` or real credentials to the repository.

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Seed the Plans

```bash
python -m scripts.seed_plans
```

This creates the Free and Pro plans.

### 7. Install Redis on your machine

Redis is required as the message broker for Celery.

On Ubuntu/Debian, install Redis Server:

```bash
sudo apt update
sudo apt install redis-server

Make sure Redis is running:

```bash
redis-cli ping
```

Expected response:

```text
PONG
```

### 8. Start the FastAPI Server

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

### 9. Start the Celery Worker

In a separate terminal, activate the virtual environment and run:

```bash
celery -A app.celery_app.celery_app worker --loglevel=info
```

The worker processes background usage-summary tasks through Redis.

### 10. Run Tests

```bash
python -m pytest
```
