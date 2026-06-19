# n8n HMAC Webhook Configuration

## What this is

JeffLocal's webhook endpoint (`/api/n8n/test-intake-batch`) verifies an HMAC-SHA256
signature on every inbound request. The signature proves the request came from the
configured n8n instance and has not been tampered with in transit.

The verification is implemented in `sandbox/dashboard/app/main.py` via
`verify_hmac_signature()` and the `verify_webhook_hmac` FastAPI dependency (IR-01).

## Required environment variable

```
JEFF_WEBHOOK_SECRET=<shared-secret>
```

- Set this on the JeffLocal server before any live traffic reaches the endpoint.
- If the variable is absent or empty, verification is **skipped** with a warning log.
  This allows local sandbox runs without a secret configured, but MUST be set before
  pilot staff accounts are active and live call data flows through the system.
- Never hardcode the secret in source code. Read from environment only.

## n8n configuration (DevOps / Saeed action)

In the n8n workflow that posts to JeffLocal:

1. Open the **HTTP Request** node that sends the webhook payload to JeffLocal.
2. Under **Headers**, add:
   ```
   Name:  X-Hub-Signature-256
   Value: sha256={{ $json.hmac_sha256 }}
   ```
3. Add a **Function** node before the HTTP Request to compute the HMAC:
   ```javascript
   const crypto = require('crypto');
   const secret = $env.JEFF_WEBHOOK_SECRET;           // set in n8n env vars
   const body   = JSON.stringify($input.first().json);
   const sig    = 'sha256=' + crypto
       .createHmac('sha256', secret)
       .update(body)
       .digest('hex');
   return [{ json: { ...$input.first().json, hmac_sha256: sig } }];
   ```
4. Set `JEFF_WEBHOOK_SECRET` in n8n's environment variables (Settings → Environment)
   to the **same value** as the server-side variable.

## Header format

```
X-Hub-Signature-256: sha256=<hex-digest>
```

The digest is computed over the **raw request body bytes** using HMAC-SHA256.
Comparison uses `hmac.compare_digest` (constant-time) to prevent timing attacks.

## Rejection behaviour

If the secret is set and the signature is missing, malformed, or does not match,
the endpoint returns HTTP 401 with:
```json
{"detail": "Invalid or missing webhook signature"}
```

No payload content is included in the response or in logs.

## Testing

Integration tests covering valid/missing/wrong-secret/tampered-body cases:
- `sandbox/dashboard/tests/test_hmac_verification.py` (14 tests, all green)
- `sandbox/dashboard/tests/test_api_endpoints.py` (HMAC section, IR-01)
