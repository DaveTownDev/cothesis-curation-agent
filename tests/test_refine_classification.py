"""Classification replay CLI — one resource_code, no full pipeline."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

CLASSIFICATION_OK = {
    "resource_type_code": "article",
    "resource_subtype_code": "methodology_paper",
    "methodology_codes": ["OBS-01"],
    "stage_codes": ["EV"],
    "relevance_score": 0.9,
    "classification_confidence": 0.85,
    "access_type": "free",
    "discipline_codes": [],
    "skill_codes": [],
}


class TestRefineClassification:
    def test_dry_run_does_not_write(self):
        from scripts.refine_classification import refine_classification_for_resource

        draft = {
            "resource_code": "test-rc",
            "title": "Chart review guide",
            "url": "https://example.com/guide",
            "resource_type_code": "article",
            "type_fields": {},
        }
        queue_doc = MagicMock()
        queue_doc.id = "queue-1"
        queue_doc.to_dict.return_value = {"draft_record": draft, "resource_code": "test-rc"}

        mock_db = MagicMock()
        mock_db.collection.return_value.where.return_value.stream.return_value = [queue_doc]
        draft_ref = MagicMock()
        draft_ref.get.return_value.exists = False
        mock_db.collection.return_value.document.return_value = draft_ref

        with patch(
            "agents.pipeline.deterministic._judge_with_retry",
            return_value=CLASSIFICATION_OK,
        ):
            result = refine_classification_for_resource("test-rc", dry_run=True, db=mock_db)

        assert result["dry_run"] is True
        assert result["patch"]["methodology_codes"] == ["OBS-01"]
        queue_doc.reference.update.assert_not_called()

    def test_missing_resource_raises(self):
        from scripts.refine_classification import refine_classification_for_resource

        mock_db = MagicMock()
        mock_db.collection.return_value.where.return_value.stream.return_value = []

        with pytest.raises(ValueError, match="not found"):
            refine_classification_for_resource("missing-rc", dry_run=True, db=mock_db)

    def test_writes_queue_and_draft_records(self):
        from scripts.refine_classification import refine_classification_for_resource

        draft = {
            "resource_code": "test-rc",
            "title": "Chart review guide",
            "url": "https://example.com/guide",
            "resource_type_code": "article",
            "type_fields": {},
        }
        queue_doc = MagicMock()
        queue_doc.id = "queue-1"
        queue_doc.to_dict.return_value = {"draft_record": draft}

        mock_db = MagicMock()
        mock_db.collection.return_value.where.return_value.stream.return_value = [queue_doc]

        def _document(name):
            ref = MagicMock()
            ref.get.return_value.exists = name in ("test-rc",)
            return ref

        mock_db.collection.return_value.document.side_effect = _document

        with patch(
            "agents.pipeline.deterministic._judge_with_retry",
            return_value=CLASSIFICATION_OK,
        ):
            result = refine_classification_for_resource("test-rc", dry_run=False, db=mock_db)

        assert result["dry_run"] is False
        queue_doc.reference.update.assert_called_once()
        updated = queue_doc.reference.update.call_args[0][0]["draft_record"]
        assert updated["methodology_codes"] == ["OBS-01"]


class TestSourceAccuracyAudit:
    def test_audit_draft_record_structure(self, monkeypatch):
        from scripts.source_accuracy_audit import audit_draft_record

        monkeypatch.setattr(
            "scripts.source_accuracy_audit.verify_source",
            lambda url, doi=None: {
                "status": "live", "code": 200, "final_url": url, "resolved": True,
            },
        )
        monkeypatch.setattr(
            "scripts.source_accuracy_audit._fetch_snippet",
            lambda url: ("chart review retrospective methodology", None),
        )

        row = audit_draft_record({
            "resource_code": "rc-1",
            "title": "Retrospective Chart Review Guide",
            "url": "https://example.com/guide",
            "resource_type_code": "article",
            "resource_subtype_code": "methodology_paper",
            "methodology_codes": ["OBS-01"],
            "editorial_description": "A guide to retrospective chart review research.",
            "summary": "How to conduct chart reviews.",
            "editorial_description_plain": "Studying patient records already collected.",
        })

        assert row["resource_code"] == "rc-1"
        assert row["source_verdict"] in ("pass", "warn", "fail")
        assert row["fetchable"] in ("yes", "no", "uncertain")
        assert "type_match" in row
        assert "hallucinations" in row
