"""
Rich Mixed Test Sender — JeffLocal
Imports the rich_mixed_pack.py fixture and writes each test call as JSON
to the outputs/handoff_json/ directory for importer processing.
"""
from __future__ import annotations

import json
from pathlib import Path

# Import the test fixture
from fixtures.rich_mixed_pack import build_rich_calls


def main() -> None:
    """
    Build all 12 rich mixed test calls and write each to
    outputs/handoff_json/{call_id}_handoff.json
    """
    output_dir = Path(__file__).resolve().parent.parent / "outputs" / "handoff_json"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build all 12 test calls
    test_calls = build_rich_calls()

    # Write each call to its own JSON file
    written_count = 0
    for call in test_calls:
        call_id = call["call_id"]
        output_path = output_dir / f"{call_id}_handoff.json"

        # Write the handoff JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(call, f, indent=2)

        print(f"✓ {call_id} → {output_path.name}")
        written_count += 1

    # Summary report
    print()
    print(f"Done — wrote {written_count} files to outputs/handoff_json/")


if __name__ == "__main__":
    main()
