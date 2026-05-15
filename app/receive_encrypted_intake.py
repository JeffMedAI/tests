import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone
from pathlib import Path

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/intake/encrypted":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")

        out_dir = Path(r"C:\JeffLocal\queue\encrypted_raw")
        out_dir.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_file = out_dir / f"{stamp}_received_from_local_intake.json"
        out_file.write_text(body, encoding="utf-8")

        response = {
            "status": "accepted",
            "stage": "jefflocal_test_receiver",
            "saved_to": str(out_file)
        }

        response_bytes = json.dumps(response).encode("utf-8")

        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8787), Handler)
    print("JeffLocal TEST receiver listening on http://0.0.0.0:8787/intake/encrypted")
    server.serve_forever()
