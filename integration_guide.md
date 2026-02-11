# Reg-Router API Integration Guide

## Overview
Reg-Router is a **Compliance-First Payment API**. Unlike standard payment gateways, we enforce SEC regulations *before* any money moves.

**The Workflow**: 
1.  **Frontend**: Collects investment intent.
2.  **Reg-Router**: Validates compliance (KYC, Limits, 506c).
3.  **Reg-Router**: Returns a "Permission Token" (Stripe Client Secret).
4.  **Frontend**: Uses the token to safely collect payment via Stripe.

---

## 1. Authentication
All API requests require a JWT token in the header.

**Get Token**:
```http
POST /api/v1/login/access-token
Content-Type: application/x-www-form-urlencoded

username=investor@example.com
password=secure_password
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "bearer"
}
```

**Use Token**:
```http
Authorization: Bearer <access_token>
```

---

## 2. The "Turnstile" Flow (How to Invest)

### Step A: The Validation Check (Backend)
Your server (or frontend) calls Reg-Router to start the transaction. We act as the "Traffic Cop."

**Request**:
```http
POST /api/v1/ledger/invest
Content-Type: application/json
Authorization: Bearer <token>

{
  "campaign_id": 456,
  "amount": 5000.00,
  "transaction_type": "investment"
}
```

**Logic Handled Automatically**:
*   **Reg CF**: Checks Income/Net Worth limits.
*   **Reg 506(b)**: Checks "Cool-off" period.
*   **Reg 506(c)**: Checks Admin Verification of documents.

**Response (Success - 200 OK)**:
Returns the `client_secret` (The Permission Token).
```json
{
  "id": 789,
  "status": "pending_payment",
  "amount": 5000.0,
  "stripe_payment_intent_id": "pi_3M...",
  "client_secret": "pi_3M..._secret_..."
}
```

**Response (Failure - 403 Forbidden)**:
If the user is not compliant.
```json
{
  "detail": "Investment exceeds SEC § 227.100 limits..."
}
```

---

### Step B: The Execution (Frontend)
Use the `client_secret` from Step A to finalize the payment using Stripe.js. **Reg-Router does not touch the card data.**

**JavaScript (Frontend)**:
```javascript
const stripe = Stripe('pk_test_...');

// 1. Call your API / Reg-Router to get the client_secret
const response = await fetch('https://api.reg-router.com/api/v1/ledger/invest', { ... });
const data = await response.json();

if (!response.ok) {
    alert("Compliance Check Failed: " + data.detail); // Show Compliance Error
    return;
}

// 2. Use the client_secret to confirm payment
const result = await stripe.confirmCardPayment(data.client_secret, {
  payment_method: {
    card: cardElement,
    billing_details: {
      name: 'Investor Name',
    },
  }
});

if (result.error) {
  // Show error to your customer
  console.log(result.error.message);
} else {
  // The payment has been processed!
  if (result.paymentIntent.status === 'succeeded') {
    alert("Investment Complete!");
  }
}
```

---

## 3. Webhooks & Settlement
Reg-Router listens for Stripe events to update the ledger.

*   `pending_payment`: Transaction created, waiting for funds.
*   `settled`: Stripe confirmed success.
*   `cancelled`: User cancelled or payment failed.

---

## 4. Admin Tools (506c Only)
For **Reg D 506(c)** deals, investors must be verified manually.

1.  **Upload Proof**: `POST /api/v1/users/me/accreditation/upload` (User uploads PDF).
2.  **Verify**: `POST /api/v1/admin/users/{id}/verify` (Admin approves).

Until verified, `POST /invest` will return `403 Forbidden`.

---

## 5. Developer Experience

### 🧪 Sandbox & Test Data
Use these "Magic Values" in your Test Environment to trigger specific compliance outcomes.

| Scenario | Income | Investment Amount | Result |
| :--- | :--- | :--- | :--- |
| **Success** | `$100,000` | `$500` | `200 OK` (Pending Payment) |
| **Reg CF Limit** | `$10,000` | `$50,000` | `403 Forbidden` (Limit Exceeded) |
| **KYC Failure** | - | - | Set `kyc_status="unverified"` in User |
| **Accredited** | - | - | Set `accreditation_status="VERIFIED_DOCS"` |

### 🛑 Error Codes Reference
Map these error codes to your UI for a better user experience.

| Error Code | Meaning | User Message Suggestion |
| :--- | :--- | :--- |
| `limit_exceeded` | Investment > Reg CF Limit | "You have hit your annual investment limit." |
| `kyc_unverified` | Identity not verified yet | "Please wait for identity verification." |
| `cool_off_period` | User < 30 days old (506b) | "You must be a member for 30 days." |
| `lockup_active` | Asset < 1 year old | "This asset cannot be sold yet." |

### 🔐 Idempotency
To prevent double-charges during network timeouts, include an `Idempotency-Key` header with a unique value (UUID).
```http
Idempotency-Key: <unique-uuid>
```
*Note: We forward this key to our banking partners to ensure safe retries.*

### 📡 Verifying Webhooks
All webhooks include a `Stripe-Signature` (or `X-Reg-Router-Signature`) header. You **must** verify this using your Webhook Secret.

```python
# Python Example
event = stripe.Webhook.construct_event(
    payload, sig_header, endpoint_secret
)
```

### 📦 SDKs
We currently support raw REST API integration.
*   **Python SDK**: *Coming Soon*
*   **Node.js SDK**: *Coming Soon*
