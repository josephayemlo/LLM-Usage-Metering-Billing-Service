# Evidence

## 1. Layered Architecture

**Requirement:** Separate data, business logic, and HTTP layers.

**Evidence:**

* `app/routers/` contains HTTP endpoints.
* `app/services/` contains business logic.
* `app/models/` contains SQLAlchemy database models.
* `app/schemas/` contains request and response validation models.
* Database access is handled through SQLAlchemy sessions and dependencies.

---

## 2. Validation at the Boundary

**Requirement:** Invalid input must return a clean 4xx response rather than causing a 500 error.

**Evidence:**

* Pydantic schemas validate request data before business logic executes.
* `UsageCreate` requires a positive usage quantity.
* `GenerateRequest` requires a non-empty prompt and non-negative token values.
* `UsageType` restricts usage types to `api_call` and `ai_token`.
* Missing resources return appropriate `404` responses.
* Quota violations return `429`.
* AI budget violations return `402`.

---

## 3. Background Job

**Requirement:** At least one background job with retry handling and failure alerting.

**Evidence:**

* Celery is configured in `app/celery_app.py`.
* Redis is used as the Celery broker/backend.
* `process_usage_summary` in `app/tasks/usage_tasks.py` processes tenant usage outside the HTTP request path.
* The task uses automatic retries with exponential backoff.
* The retry configuration allows up to 3 retries.
* `on_failure()` logs a critical alert when the task permanently fails.

---

## 4. Real Persistence

**Requirement:** Use a real database with migrations, indexes, and tenant isolation.

**Evidence:**

* PostgreSQL is used as the production database.
* Alembic manages database migrations.
* Core entities are persisted using SQLAlchemy models.
* Usage events are associated with `tenant_id`.
* The usage-event idempotency constraint is scoped by tenant:
  `tenant_id + idempotency_key`.
* Usage queries filter by `tenant_id`, preventing usage from being aggregated across tenants.

---

## 5. Idempotency

**Requirement:** Retried billable requests must not create duplicate usage.

**Evidence:**

* `UsageEvent` has a unique constraint on `(tenant_id, idempotency_key)`.
* `record_usage()` first checks for an existing event using the tenant and idempotency key.
* A database `IntegrityError` is also handled to protect against concurrent duplicate requests.
* Tests verify that repeating a request with the same idempotency key returns the existing usage event.

**Payment webhook evidence:**

* `PaymentEvent.event_id` is unique.
* Paystack webhook processing checks whether the event has already been processed.
* Replayed webhook events return `already_processed` without changing the subscription again.

---

## 6. Secrets

**Requirement:** Secrets must not be committed to the repository.

**Evidence:**

* Paystack credentials and database configuration are loaded from environment variables.
* `.env` is excluded through `.gitignore`.
* `.env.example` contains safe placeholder values.
* No real Paystack secret key is stored in the source code.

---

## 7. AI Cost Tracking

**Requirement:** AI usage must have cost tracking and a budget guard.

**Evidence:**

* AI usage events store `cost_micro_units`.
* `pricing_service.py` calculates costs using integer micro-units rather than floating-point money calculations.
* Uncached input, cached input, output, and reasoning tokens have separate pricing rules.
* Reasoning tokens are charged using the output-token rate.
* `budget_service.py` calculates the current AI spend for the tenant's billing period.
* Requests are rejected with `402` when the configured AI budget would be exceeded.
* The `/generate/` endpoint records both token usage and calculated cost.

---

## 8. Quota Enforcement

**Requirement:** Usage limits must be enforced accurately at the quota boundary.

**Evidence:**

* `quota_service.py` retrieves the tenant's active subscription and plan.
* Usage is calculated only within the subscription's current billing period.
* The quota check uses:

```text
current_usage + requested_quantity <= plan_limit
```

* The exact quota boundary is therefore allowed.
* A request that would exceed the limit is rejected with `429` and the message `usage quota exceeded`.
* Automated tests cover the quota boundary.

---

## 9. Token Pricing

**Requirement:** Token pricing must correctly account for cached input and reasoning tokens.

**Evidence:**

* `pricing_service.py` separates cached and uncached input tokens.
* Cached input uses a lower price than regular input.
* Output and reasoning tokens are charged using the output rate.
* The implementation does not simply add independent category prices incorrectly.
* Automated pricing tests verify the expected totals.

---

## 10. Paystack Payment Flow

**Requirement:** Implement a complete payment-provider test flow.

**Evidence:**

* Paystack transaction initialization is implemented in `paystack_service.py`.
* The payment amount is taken from the selected plan price.
* Payment verification checks the Paystack transaction status.
* The verified payment amount is compared against the plan price.
* A successful payment activates the tenant subscription.
* Subscription billing-period start and end dates are updated after successful payment.
* The implementation uses Paystack test-mode credentials.

---

## 11. Webhook Security

**Requirement:** Webhooks must verify authenticity and be idempotent.

**Evidence:**

* The Paystack webhook reads the `x-paystack-signature` header.
* The request body is verified using HMAC-SHA512 and the Paystack secret key.
* Invalid signatures return `401`.
* The webhook checks the transaction amount against the subscription plan.
* Processed events are stored in `PaymentEvent`.
* Duplicate webhook events are detected and ignored.
* Automated tests cover invalid signatures, successful processing, and duplicate events.

---

## 12. Billing Period Isolation

**Requirement:** Usage calculations must respect the active subscription billing period.

**Evidence:**

* Usage aggregation accepts `period_start` and `period_end`.
* Queries use:

```text
created_at >= period_start
created_at < period_end
```

* Quota enforcement uses the subscription's current billing period.
* Tenant usage totals use the same billing-period boundaries.
* The Celery usage-summary task also calculates usage within the active billing period.
