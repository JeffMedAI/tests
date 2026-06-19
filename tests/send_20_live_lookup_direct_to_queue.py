import sys
import time
import json
import subprocess
from pathlib import Path


FIXTURE_DIR = Path(r"C:\JeffLocal\tests\fixtures")
sys.path.insert(0, str(FIXTURE_DIR))

import live_lookup_test_payloads as pack


LOCAL_ENCRYPTED_RAW_DIR = Path(r"C:\JeffLocal\queue\encrypted_raw")

SCHEDULED_TASK_NAME = "JeffLocal Encrypted Intake Cycle"
TRIGGER_SCHEDULED_TASK_AFTER_SEND = True


def write_envelope_to_local_queue(envelope):
    LOCAL_ENCRYPTED_RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = LOCAL_ENCRYPTED_RAW_DIR / f"{envelope['message_id']}.json"
    out_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    return out_path


def trigger_scheduled_task():
    if not TRIGGER_SCHEDULED_TASK_AFTER_SEND:
        return

    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f'Start-ScheduledTask -TaskName "{SCHEDULED_TASK_NAME}"',
        ],
        check=False,
    )


def main():
    calls = pack.build_calls()

    print("Writing 20 live-style encrypted calls to local encrypted queue:")
    print(LOCAL_ENCRYPTED_RAW_DIR)
    print()

    written_count = 0

    for i, call in enumerate(calls, start=1):
        envelope = pack.encrypt_envelope(call)
        out_path = write_envelope_to_local_queue(envelope)
        written_count += 1

        print(f"[{i}/20] {call['request_type']}")
        print(f"  call_id: {call['call_id']}")
        print(f"  caller supplied name: {call['normalized_input']['patient_name']}")
        print(f"  caller supplied dob: {call['normalized_input']['dob']}")
        print(f"  callback from caller ID: {call['normalized_input']['callback_number'] or '(withheld/unavailable)'}")
        print(f"  local envelope: {out_path}")
        print()

        time.sleep(0.5)

    print(f"Wrote {written_count}/20 local encrypted envelopes.")
    print("Triggering JeffLocal scheduled cycle...")
    trigger_scheduled_task()


if __name__ == "__main__":
    main()
