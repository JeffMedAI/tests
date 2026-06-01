"""Inject a fresh E2E batch into the sandbox dashboard via direct-intake."""
import sys, json, urllib.request, urllib.error
sys.path.insert(0, r'C:\JeffLocal\tests\fixtures')
from e2e_callflow_pack import build_e2e_batch, _ts

ts = _ts()
batch = build_e2e_batch(ts)
call_ids = [c['call_id'] for c in batch['calls']]
print('Batch ID:', batch['batch_id'])
print('Calls:', len(call_ids))
for cid in call_ids:
    print(' ', cid)

url = 'http://localhost:5000/api/n8n/test-intake-batch'
calls = batch['calls']
total_imported = 0

for i in range(0, len(calls), 5):
    chunk = calls[i:i + 5]
    payload = {
        'test_mode': True,
        'batch_id': batch['batch_id'] + f'-chunk{i // 5}',
        'disable_google_push': True,
        'refresh_artifacts': i == 0,
        'calls': chunk,
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.loads(r.read())
            imp = body.get('dashboard_imported', 0)
            total_imported += imp
            print(f'Chunk {i // 5}: HTTP {r.status} imported={imp} '
                  f'processed={body.get("batch_processed","?")} '
                  f'handoffs={body.get("batch_handoffs","?")}')
    except urllib.error.HTTPError as e:
        print(f'Chunk {i // 5}: HTTP {e.code} ERROR - {e.read().decode()}')
    except Exception as e:
        print(f'Chunk {i // 5}: ERROR - {e}')

print(f'\nTotal imported: {total_imported}')
print('\nCall IDs:')
for cid in call_ids:
    print(' ', cid)
