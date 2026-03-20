import os
import csv
import json
import sys
from typing import Any, Dict, List

def flatten_record(record: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """
    Flatten one JSON object.
    Example:
      {"a": {"b": 1}, "c": 2} -> {"a__b": 1, "c": 2}
    """
    out = {}
    for k, v in record.items():
        col = f"{prefix}__{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten_record(v, col))
        else:
            out[col] = v
    return out

def build_rows_from_top_level(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build CSV rows from top-level JSON keys.
    - If top-level value is a list of objects => flattened with <topkey>__<field>
    - If top-level value is a list of primitives => <topkey>
    - If top-level value is object => treated as single item list
    - If top-level value is primitive => treated as single item list

    Rows are created using max length across all top-level keys.
    For row i, each section uses i-th element if available, else blanks.
    """
    prepared: Dict[str, List[Dict[str, Any]]] = {}

    for top_key, value in json_data.items():
        rows_for_key: List[Dict[str, Any]] = []

        if isinstance(value, list):
            if len(value) == 0:
                rows_for_key = []
            else:
                for item in value:
                    if isinstance(item, dict):
                        flat = flatten_record(item, top_key)
                        rows_for_key.append(flat)
                    else:
                        rows_for_key.append({top_key: item})

        elif isinstance(value, dict):
            rows_for_key = [flatten_record(value, top_key)]
        else:
            rows_for_key = [{top_key: value}]

        prepared[top_key] = rows_for_key

    max_len = max((len(v) for v in prepared.values()), default=0)

    all_rows: List[Dict[str, Any]] = []
    for i in range(max_len):
        row: Dict[str, Any] = {}
        for top_key, rows in prepared.items():
            if i < len(rows):
                row.update(rows[i])
        all_rows.append(row)

    return all_rows

def write_csv(rows: List[Dict[str, Any]], output_csv_path: str) -> None:
    # Collect all columns in order of first appearance
    fieldnames: List[str] = []
    seen = set()

    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)

    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)

    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def get_base_dir() -> str:
    # In PyInstaller one-file mode, use the executable's folder.
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resolve_runtime_dirs() -> tuple[str, str]:
    base_dir = get_base_dir()
    candidates = [
        base_dir,
        os.path.dirname(base_dir),
        os.getcwd(),
    ]

    for candidate in candidates:
        source_dir = os.path.join(candidate, "source")
        result_dir = os.path.join(candidate, "result")
        if os.path.isdir(source_dir):
            return source_dir, result_dir

    # Default to base dir even if source is missing, so error message is explicit.
    return os.path.join(base_dir, "source"), os.path.join(base_dir, "result")


def pick_source_json(source_folder_path: str) -> str:
    if not os.path.isdir(source_folder_path):
        raise FileNotFoundError(f"Source folder not found: {source_folder_path}")

    json_files = [
        os.path.join(source_folder_path, name)
        for name in os.listdir(source_folder_path)
        if name.lower().endswith(".json") and os.path.isfile(os.path.join(source_folder_path, name))
    ]

    if not json_files:
        raise FileNotFoundError(f"No JSON file found in source folder: {source_folder_path}")

    # Pick the most recently modified JSON file when multiple files exist.
    json_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return json_files[0]

def convert_json_to_csv(source_json_path: str, result_folder_path: str, output_filename: str = None) -> str:
    if not os.path.isfile(source_json_path):
        raise FileNotFoundError(f"Source JSON file not found: {source_json_path}")

    with open(source_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Top-level JSON must be an object/dictionary (as in your sample).")

    rows = build_rows_from_top_level(data)

    # if output_filename is None:
    #     base = os.path.splitext(os.path.basename(source_json_path))[0]
    #     output_filename = f"{base}.csv"

    output_filename = "result.csv"

    output_csv_path = os.path.join(result_folder_path, output_filename)
    write_csv(rows, output_csv_path)
    return output_csv_path

def main():
    source_dir, result_dir = resolve_runtime_dirs()

    try:
        source_json = pick_source_json(source_dir)
        output_path = convert_json_to_csv(source_json, result_dir, "result.csv")
        print(f"CSV created from {os.path.basename(source_json)}")
        print(f"Output: {output_path}")
    except Exception as exc:
        print(f"Error: {exc}")
        raise

if __name__ == "__main__":
    main()
