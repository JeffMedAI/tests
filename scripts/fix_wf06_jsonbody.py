import json, sqlite3, urllib.request

conn = sqlite3.connect(r'C:\Users\s5256\.n8n\database.sqlite')
key = conn.execute('SELECT apiKey FROM user_api_keys LIMIT 1').fetchone()[0]
conn.close()

headers = {'X-N8N-API-KEY': key, 'Content-Type': 'application/json'}

req = urllib.request.Request('http://localhost:5678/api/v1/workflows/0pRmm3xCHP4wsVyy', headers=headers)
wf = json.loads(urllib.request.urlopen(req).read())

# Correct n8n expression with double-brace delimiters.
# Passes batch_id and call_id straight through from Jeff payload.
# Fallback: plain timestamp (no prefix) if batch_id missing.
new_json_body = (
    "={{\n"
    "  {\n"
    '    batch_id: $json.body.batch_id || $now.toFormat("yyyyMMdd-HHmmss"),\n'
    "    test_mode: true,\n"
    "    disable_google_push: true,\n"
    '    source: "n8n_test_webhook",\n'
    "    calls: [\n"
    "      $json.body\n"
    "    ]\n"
    "  }\n"
    "}}"
)

for node in wf['nodes']:
    if node['type'] == 'n8n-nodes-base.httpRequest':
        node['parameters']['jsonBody'] = new_json_body
        print('Patched:', node['name'])

body = json.dumps({
    'name': wf['name'],
    'nodes': wf['nodes'],
    'connections': wf['connections'],
    'settings': {'executionOrder': 'v1'},
    'staticData': None,
    'pinData': {}
}).encode()

# Deactivate
req = urllib.request.Request('http://localhost:5678/api/v1/workflows/0pRmm3xCHP4wsVyy/deactivate',
                              headers=headers, method='POST', data=b'')
urllib.request.urlopen(req)

# Update
req = urllib.request.Request('http://localhost:5678/api/v1/workflows/0pRmm3xCHP4wsVyy',
                              headers=headers, method='PUT', data=body)
result = json.loads(urllib.request.urlopen(req).read())
http_node = next(n for n in result['nodes'] if n['type'] == 'n8n-nodes-base.httpRequest')
print('Saved jsonBody:')
print(http_node['parameters']['jsonBody'])

# Reactivate
req = urllib.request.Request('http://localhost:5678/api/v1/workflows/0pRmm3xCHP4wsVyy/activate',
                              headers=headers, method='POST', data=b'')
urllib.request.urlopen(req)
print('Reactivated.')
