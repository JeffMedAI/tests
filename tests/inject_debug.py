"""Debug inject — shows full error body."""
import sys, json, urllib.request, urllib.error
sys.path.insert(0, r'C:\JeffLocal\tests\fixtures')
from e2e_callflow_pack import build_e2e_batch, _ts

ts = _ts()
batch = build_e2e_batch(ts)
calls = batch['calls'][:1]  # just one call for debug

payload = {
    'test_mode': True,
    'batch_id': 'DEBUG-' + ts,
    'disable_google_push': True,
    'refresh_artifacts': False,
    'calls': calls,
}
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(
    'http://localhost:5000/api/n8n/test-intake-batch',
    data=data,
    headers={'Content-Type': 'application/json'},
)
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        print('OK:', r.status, json.loads(r.read()))
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='replace')
    print(f'HTTP {e.code}:')
    try:
        print(json.dumps(json.loads(body), indent=2))
    except Exception:
        print(body[:2000])
except Exception as e:
    print('ERROR:', e)
