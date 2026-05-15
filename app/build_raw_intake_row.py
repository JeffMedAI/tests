import argparse
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_MAPPING_PATH = Path(r"C:\JeffLocal\config\raw_intake_columns.json")


def _get_path(data, path):
    current = data
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _first_value(data, paths, default):
    for path in paths:
        value = _get_path(data, path)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    if default == "__NOW__":
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return default


def _format_value(value, value_type=None):
    if value_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "yes", "1"}
        return bool(value)
    if value_type == "number":
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return value
        return value
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return value


def load_mapping(mapping_path=DEFAULT_MAPPING_PATH):
    with Path(mapping_path).open("r", encoding="utf-8") as f:
        mapping = json.load(f)
    return mapping["columns"]


def build_raw_intake_row(handoff, mapping_path=DEFAULT_MAPPING_PATH):
    columns = load_mapping(mapping_path)
    row = OrderedDict()
    for column in columns:
        value = _first_value(handoff, column.get("paths", []), column.get("default", ""))
        row[column["header"]] = _format_value(value, column.get("type"))
    return row


def main():
    parser = argparse.ArgumentParser(description="Build a Raw Intake row from a JeffLocal handoff JSON file.")
    parser.add_argument("handoff_json")
    parser.add_argument("--mapping", default=str(DEFAULT_MAPPING_PATH))
    args = parser.parse_args()

    with Path(args.handoff_json).open("r", encoding="utf-8-sig") as f:
        handoff = json.load(f)

    row = build_raw_intake_row(handoff, args.mapping)
    print(json.dumps(row, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
