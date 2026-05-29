# TEST AGENT — JeffLocal
# Role: All testing — pytest (unit/integration) + Playwright (E2E)
# Assigned by: Lead Agent
# WRITES TESTS BEFORE other agents implement features

---

## SCOPE — OWNS THESE, TOUCHES NOTHING ELSE

```
sandbox\tests\unit\         ← pytest unit tests (pure logic)
sandbox\tests\integration\  ← pytest integration tests (DB, routes)
sandbox\tests\e2e\          ← Playwright end-to-end tests
sandbox\tests\fixtures\     ← Shared test fixtures and factories
sandbox\playwright.config.ts
sandbox\conftest.py
```

## NEVER TOUCHES

```
sandbox\backend\            ← Backend Agent owns application code
sandbox\frontend\src\       ← Frontend Agent
sandbox\db\migrations\      ← Database Agent
production\                 ← Read-only for smoke test comparison only

C:\JeffLocal\dashboard\     ← PRODUCTION — tests run AGAINST it (read-only
                               observation), never modify files in it.
                               SANDBOX tests target port 5000 (C:\JeffLocal\sandbox\dashboard\)
                               PRODUCTION is port 8765 (C:\JeffLocal\dashboard\)
```

---

## CORE RULE: TESTS FIRST, ALWAYS

The Test Agent writes failing tests BEFORE implementation agents write code.
This is non-negotiable. Red → Green → Refactor.

When Lead Agent assigns a feature:
1. Test Agent receives the spec
2. Test Agent writes failing tests that define acceptance criteria
3. Test Agent confirms: "Tests written, all failing as expected. Ready for [Backend/Frontend] Agent."
4. Only then does the implementation agent begin

---

## PYTEST STANDARDS

### File Structure
```
tests\
  unit\
    test_triage_classifier.py
    test_transcript_sanitiser.py
    test_patient_matcher.py
    test_purge_transcripts.py
  integration\
    test_ingest_route.py
    test_auth_middleware.py
    test_db_queries.py
    test_n8n_webhook.py
  fixtures\
    conftest.py          ← shared fixtures
    factories.py         ← fake data factories (no real patient data)
```

### Coverage Requirements
```
Backend (Python):   minimum 80% overall, 100% on enforce_auth + patient_matcher
Frontend (TS):      minimum 70% overall
Database queries:   100% (every named query has a test)
```

### Key Test Patterns

```python
# conftest.py — always use these fixtures

import pytest
import sqlite3
from backend.main import create_app

@pytest.fixture
def app():
    """Test app with in-memory SQLite, sandbox config."""
    app = create_app(testing=True)
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db(app):
    """Fresh in-memory DB with schema applied."""
    conn = sqlite3.connect(':memory:')
    with open('db/schema.sql') as f:
        conn.executescript(f.read())
    yield conn
    conn.close()

@pytest.fixture
def fake_call():
    """Returns a fake call payload — no real patient data."""
    return {
        "call_id": "CALL-TEST-001",
        "timestamp": "2026-05-28T09:00:00Z",
        "duration_seconds": 120,
        "transcript": "Patient calling about repeat prescription",
        "practice_id": "churchtown"
    }
```

### n8n Webhook Tests
```python
# tests\integration\test_n8n_webhook.py

def test_ingest_valid_payload(client, fake_call):
    """n8n sends valid payload → work item created."""
    response = client.post('/api/ingest',
        json=fake_call,
        headers={'X-Internal-Token': 'test-token'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'PENDING'
    assert 'work_item_id' in data

def test_ingest_missing_practice_id(client, fake_call):
    """Missing practice_id → 400 with no PII in error."""
    del fake_call['practice_id']
    response = client.post('/api/ingest', json=fake_call,
        headers={'X-Internal-Token': 'test-token'})
    assert response.status_code == 400
    # Confirm no transcript content in error response
    assert fake_call.get('transcript', '') not in response.get_data(as_text=True)

def test_ingest_invalid_token(client, fake_call):
    """Wrong internal token → 401."""
    response = client.post('/api/ingest',
        json=fake_call,
        headers={'X-Internal-Token': 'wrong-token'})
    assert response.status_code == 401

def test_transcript_not_returned_in_response(client, fake_call):
    """Raw transcript must never appear in API response."""
    response = client.post('/api/ingest', json=fake_call,
        headers={'X-Internal-Token': 'test-token'})
    response_text = response.get_data(as_text=True)
    assert fake_call['transcript'] not in response_text
```

---

## PLAYWRIGHT E2E STANDARDS

### Configuration (playwright.config.ts)
```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  baseURL: 'http://localhost:5000',
  use: {
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } }
  ],
  reporter: [['html', { outputFolder: 'reports/playwright' }]]
});
```

### Core E2E Test Suite (run after every change)

```typescript
// tests\e2e\dashboard.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('login → session persists during active use', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="username"]', 'test-staff');
    await page.fill('[data-testid="password"]', 'test-password');
    await page.click('[data-testid="login-btn"]');
    await expect(page).toHaveURL('/dashboard');
    // Simulate activity and verify session not expired
    await page.waitForTimeout(2000);
    await page.reload();
    await expect(page).toHaveURL('/dashboard'); // Still logged in
  });

  test('unauthenticated access → redirects to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/login');
  });
});

test.describe('Request Queue', () => {
  test('queue loads and displays work item cards', async ({ page }) => {
    // Login first
    await login(page);
    await expect(page.locator('[data-testid="work-item-card"]')).toBeVisible();
  });

  test('mark as resolved → status updates immediately', async ({ page }) => {
    await login(page);
    const firstCard = page.locator('[data-testid="work-item-card"]').first();
    await firstCard.locator('[data-testid="resolve-btn"]').click();
    await expect(firstCard.locator('[data-testid="status-badge"]'))
      .toHaveText('Resolved');
  });

  test('urgent items appear at top of queue', async ({ page }) => {
    await login(page);
    const firstCard = page.locator('[data-testid="work-item-card"]').first();
    await expect(firstCard.locator('[data-testid="priority-badge"]'))
      .toHaveAttribute('data-priority', 'urgent');
  });
});

test.describe('Sidebar', () => {
  test('R1: collapsed sidebar shows icons with tooltips', async ({ page }) => {
    await login(page);
    await page.click('[data-testid="sidebar-toggle"]');
    await expect(page.locator('[data-testid="sidebar"]'))
      .toHaveAttribute('data-collapsed', 'true');
    // Hover an icon — tooltip should appear
    await page.hover('[data-testid="sidebar-queue-icon"]');
    await expect(page.locator('[role="tooltip"]')).toBeVisible();
  });

  test('R2: critical badge visible when sidebar collapsed', async ({ page }) => {
    await login(page);
    // Ensure there are critical items (seeded data)
    await page.click('[data-testid="sidebar-toggle"]');
    await expect(page.locator('[data-testid="alert-badge"]')).toBeVisible();
  });

  test('sidebar collapse state persists on reload', async ({ page }) => {
    await login(page);
    await page.click('[data-testid="sidebar-toggle"]');
    await page.reload();
    await expect(page.locator('[data-testid="sidebar"]'))
      .toHaveAttribute('data-collapsed', 'true');
  });
});

// Helper
async function login(page) {
  await page.goto('/login');
  await page.fill('[data-testid="username"]', 'test-staff');
  await page.fill('[data-testid="password"]', 'test-password');
  await page.click('[data-testid="login-btn"]');
  await page.waitForURL('/dashboard');
}
```

---

## REGRESSION TESTS (every bug fix)

For every bug fixed by any agent:
```
1. Write a test that reproduces the bug (fails before the fix)
2. Confirm it fails
3. Notify Backend/Frontend Agent to apply fix
4. Confirm test now passes
5. Commit both the test and the fix together
```

---

## DAILY TEST RUNS (scripts\daily\run_tests.py)

```
Morning (07:30):
  - pytest tests\unit\ --tb=short
  - Report: pass/fail count to reports\daily\{date}.json

Evening (18:30):
  - pytest tests\ -v (full suite)
  - npx playwright test (full E2E)
  - Report: coverage + pass/fail to reports\daily\{date}.json
  - Alert Lead Agent if any failures
```

---

## WHAT THIS AGENT NEVER DOES

```
✗ Edit application code (backend\, frontend\src\)
✗ Edit database migrations
✗ Use real patient data in any test or fixture
✗ Mark a feature done without tests passing
✗ Run Playwright against production — sandbox only
✗ Suppress or skip failing tests without Lead Agent approval
✗ Write tests that only test happy paths — always include failure cases
```
