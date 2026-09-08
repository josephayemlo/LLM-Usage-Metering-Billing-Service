## Plans

### Free Plan

![Free plan](screenshots/get_free_plan.png)

This screenshot shows that the Free plan was successfully seeded and can be retrieved from the database.

### Pro Plan

![Pro plan](screenshots/get_pro_plan.png)

This screenshot shows that the Pro plan was successfully seeded and can be retrieved from the database.

## Tenant

### Tenant Creation

![Tenant creation](screenshots/post_tenant.png)

This screenshot shows a tenant being successfully created through the tenant endpoint.

### Automatic Free Subscription

![Tenant automatically creates Free subscription](screenshots/created_tenant_auto_creates_subscription_with_free_plan.png)

This screenshot shows that creating a tenant automatically creates an active subscription using the Free plan.

### Get All Tenants

![Get all tenants](screenshots/get_all_tenants.png)

This screenshot shows the successful retrieval of tenants from the system.



##  Idempotency

The usage metering endpoint prevents the same billable action from being recorded more than once when a request is retried with the same idempotency key.

### Usage Before Retry

![Usage before retry](screenshots/usage_check_before.png)

This screenshot shows the tenant's usage events before the retry request was sent.

### Repeated Request Using the Same Idempotency Key

![Request using existing idempotency key](screenshots/request_using_existing_indempotency.png)

The same usage request is sent again using the existing idempotency key. The response heading/time confirms that this is a separate request from the initial usage check.

### Usage After Retry

![Usage after retry](screenshots/usage_check_after.png)

The usage events are checked again after the repeated request. The usage list remains unchanged, demonstrating that the repeated request did not create an additional usage event or increase the recorded usage.


## Quotas

### Quota Enforcement

![Quota enforcement exceeded](screenshots/quota_enforcement_exceeded.png)

This screenshot shows a request being rejected after the tenant exceeds the usage quota defined by the active plan. The API returns the appropriate error response and explains that the usage quota has been exceeded.



## Payment 

The payment initialization endpoint prevents duplicate pending payments when the same initialization request is sent more than once.

### First Initialization Request

![First payment initialization](screenshots/initialize_payment_first_time.png)

The first request initializes a new payment and returns a payment reference and authorization details.

### Second Initialization Request

![Second payment initialization](screenshots/initialize_payment_second_time.png)

The initialization request is sent again. The response heading/time confirms that this is a new request, while the payment reference remains the same. The existing pending payment is returned instead of creating another payment.

### Initialization After Payment

![Payment initialization after payment](screenshots/initialize_payment_after_paying.png)

After the payment is completed, the initialization endpoint is called again. The system recognizes the existing paid payment and returns its paid status rather than creating a new payment.


### Payment Started

![Paystack payment started](screenshots/payment_start_paystack.png)

### Payment Successful

![Successful Paystack payment](screenshots/payment_successful_paystack.png)


## Subscription

### Pending Subscription

![Pending subscription](screenshots/pending_subscription.png)

This screenshot shows a subscription in the **pending** state before successful payment.

### Active Subscription

![Active subscription](screenshots/active_subscription.png)

This screenshot shows the subscription becoming **active** after successful payment.


## Automated Tests

![Pytest test results](screenshots/test.png)

This screenshot shows the project's automated test suite being executed successfully with pytest.
