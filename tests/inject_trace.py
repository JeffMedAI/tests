"""Run test-intake-batch via httpx TestClient to get Python traceback."""
import sys, json
sys.path.insert(0, r'C:\JeffLocal\sandbox\dashboard')
sys.path.insert(0, r'C:\JeffLocal\tests\fixtures')

import os
os.environ['JEFF_WEBHOOK_SECRET'] = ''

from app.main import app
from httpx import AsyncClient, ASGITransport
import asyncio

from e2e_callflow_pack import build_e2e_batch, _ts

async def run():
    ts = _ts()
    batch = build_e2e_batch(ts)
    payload = {
        'test_mode': True,
        'batch_id': 'DEBUG-' + ts,
        'disable_google_push': True,
        'refresh_artifacts': False,
        'calls': batch['calls'][:1],
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        r = await client.post('/api/n8n/test-intake-batch', json=payload)
        print(f'HTTP {r.status_code}')
        try:
            print(json.dumps(r.json(), indent=2))
        except Exception:
            print(r.text[:3000])

asyncio.run(run())
