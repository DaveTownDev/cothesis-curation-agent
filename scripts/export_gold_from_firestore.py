"""
Export eval_gold_cases from Firestore to eval/cases/*.json.

Cloud Run console writes gold cases to Firestore; this script materialises them
for local aggregate / adk eval workflows.

  python -m scripts.export_gold_from_firestore
  python -m scripts.export_gold_from_firestore --out eval/cases
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "eval" / "cases"
COLLECTION = "eval_gold_cases"
FIRESTORE_ONLY_KEYS = frozenset({"updated_at"})


def export_cases(out_dir: Path = DEFAULT_OUT) -> int:
    from google.cloud import firestore

    client = firestore.Client()
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for snap in client.collection(COLLECTION).stream():
        data = dict(snap.to_dict() or {})
        for key in FIRESTORE_ONLY_KEYS:
            data.pop(key, None)
        if "eval_id" not in data:
            data["eval_id"] = snap.id
        path = out_dir / f"{snap.id}.json"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Export eval_gold_cases from Firestore")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    n = export_cases(args.out)
    print(f"Exported {n} cases -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
