from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
if str(FIXTURE_DIR) not in sys.path:
    sys.path.insert(0, str(FIXTURE_DIR))

from n8n_webhook_test_pack import build_batch  # noqa: E402


LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def is_local_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.hostname in LOCAL_HOSTS


def main() -> int:
    parser = argparse.ArgumentParser(description="Send 5 encrypted N8NTEST calls to a local n8n webhook.")
    parser.add_argument("--url", required=True, help="Local n8n webhook URL.")
    parser.add_argument("--allow-nonlocal", action="store_true", help="Allow a non-local URL. Not recommended for this test.")
    args = parser.parse_args()

    if not args.url.strip():
        print("ERROR: --url is required", file=sys.stderr)
        return 2
    if not args.allow_nonlocal and not is_local_url(args.url):
        print("ERROR: refusing non-local webhook URL without --allow-nonlocal", file=sys.stderr)
        return 2

    batch_id = "N8NTEST-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    payload = build_batch(batch_id)
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        args.url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        print(json.dumps({"ok": False, "status": exc.code, "response": response_body}, indent=2))
        return 1

    try:
        parsed = json.loads(response_body)
    except json.JSONDecodeError:
        parsed = {"raw_response": response_body}
    print(json.dumps(parsed, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
