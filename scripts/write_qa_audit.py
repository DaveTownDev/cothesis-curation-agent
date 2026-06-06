"""
Merge the two re-audit layers into a single `qa_audit` map on each review_queue doc.

Inputs (both keyed by resource_code):
  /tmp/cothesis_audit.json            -> data-quality + URL liveness (scripts.audit_records)
  /tmp/cothesis_source_accuracy.json  -> source-accuracy verdicts from the Claude workflow,
                                         a list of {resource_code, source_verdict, fetchable,
                                         type_match, methodology_plausible, description_accurate,
                                         source_issues[], hallucinations[], source_notes}

Writes review_queue.{doc}.qa_audit so the console QA column/panel render the re-audit.

  GOOGLE_CLOUD_PROJECT=cothesis-curation-agent .venv/bin/python -m scripts.write_qa_audit
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

AUDIT = "/tmp/cothesis_audit.json"
ACCURACY = "/tmp/cothesis_source_accuracy.json"


def main() -> int:
    project = os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "cothesis-curation-agent")
    from google.cloud import firestore
    db = firestore.Client(project=project)

    audit = {r["resource_code"]: r for r in json.load(open(AUDIT))["records"] if r.get("resource_code")}
    acc = {}
    if os.path.exists(ACCURACY):
        for r in json.load(open(ACCURACY)):
            if r.get("resource_code"):
                acc[r["resource_code"]] = r
    else:
        print(f"WARN: {ACCURACY} not found — writing data-quality/URL layer only")

    checked_at = datetime.now(timezone.utc).isoformat()
    verdicts = Counter()
    written = 0
    for doc in db.collection("review_queue").stream():
        d = doc.to_dict()
        rc = d.get("resource_code")
        a = audit.get(rc, {})
        s = acc.get(rc, {})
        qa = {
            "checked_at": checked_at,
            "data_quality": a.get("dq"),
            "dq_issues": [f"{i['sev']}:{i['field']}:{i['msg']}" for i in a.get("issues", [])],
            "url_status": a.get("url_status"),
            "url_code": a.get("url_code"),
            "source_verdict": s.get("source_verdict"),
            "fetchable": s.get("fetchable"),
            "type_match": s.get("type_match"),
            "methodology_plausible": s.get("methodology_plausible"),
            "description_accurate": s.get("description_accurate"),
            "source_issues": s.get("source_issues", []),
            "hallucinations": s.get("hallucinations", []),
            "source_notes": s.get("source_notes"),
        }
        doc.reference.update({"qa_audit": qa})
        written += 1
        if s.get("source_verdict"):
            verdicts[s["source_verdict"]] += 1
    print(f"Wrote qa_audit to {written} review_queue docs")
    print("Source verdicts:", dict(verdicts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
