"""Additional editorial + reconciliation coverage tests."""
import pytest
from unittest.mock import MagicMock, patch


class TestParseEditorialJson:

    VALID = {
        "editorial_description": "A key reporting checklist.",
        "summary": "PRISMA 2020 covers 27 items across searching, screening, and synthesis.",
        "editorial_description_plain": "A checklist for writing up studies that combine research.",
        "proposed_badges": ["essential"],
        "difficulty_level": "beginner",
    }

    def test_valid_json_parses(self):
        from agents.editorial.tools import parse_editorial_json
        out = parse_editorial_json(self.VALID)
        assert out.editorial_description == "A key reporting checklist."

    def test_non_dict_raises(self):
        from agents.editorial.tools import parse_editorial_json
        with pytest.raises(ValueError, match="not a dict"):
            parse_editorial_json("just a string")

    def test_invalid_badge_raises(self):
        from agents.editorial.tools import parse_editorial_json
        from pydantic import ValidationError
        bad = {**self.VALID, "proposed_badges": ["not_real"]}
        with pytest.raises(ValidationError):
            parse_editorial_json(bad)

    def test_jargon_in_plain_logs_warning(self, caplog):
        import logging
        from agents.editorial.tools import parse_editorial_json
        jargon = {**self.VALID,
                  "editorial_description_plain": "Covers systematic review methods."}
        import logging
        with caplog.at_level(logging.WARNING, logger="agents.editorial.tools"):
            out = parse_editorial_json(jargon, resource_code="test-001")
        assert "Jargon detected" in caplog.text

    def test_clean_plain_does_not_warn(self, caplog):
        import logging
        from agents.editorial.tools import parse_editorial_json
        with caplog.at_level(logging.WARNING, logger="agents.editorial.tools"):
            parse_editorial_json(self.VALID, resource_code="test-002")
        assert "Jargon" not in caplog.text


class TestClassificationExceptionPaths:

    def test_non_dict_returns_none(self):
        """Non-dict input (e.g. raw string) returns None as the retry signal."""
        from agents.classification.tools import parse_classification_json
        result = parse_classification_json("not a dict")
        assert result is None

    def test_missing_required_field_raises_validation_error(self):
        """Missing required fields raises ValidationError (caller routes review_needed)."""
        from agents.classification.tools import parse_classification_json
        from pydantic import ValidationError
        incomplete = {"resource_type_code": "article"}  # missing relevance_score etc.
        with pytest.raises(ValidationError):
            parse_classification_json(incomplete)

    def test_none_input_returns_none(self):
        from agents.classification.tools import parse_classification_json
        result = parse_classification_json(None)
        assert result is None


class TestFetchExistingTitles:

    def test_returns_list_of_title_dicts(self):
        from agents.reconciliation.tools import fetch_existing_titles

        mock_doc1 = MagicMock()
        mock_doc1.id = "prisma-2020"
        mock_doc1.get.side_effect = lambda k, d=None: {"title": "PRISMA 2020 Statement"}.get(k, d)

        mock_doc2 = MagicMock()
        mock_doc2.id = "strobe-2007"
        mock_doc2.get.side_effect = lambda k, d=None: {"title": "STROBE Statement"}.get(k, d)

        mock_col = MagicMock()
        mock_col.select.return_value.limit.return_value.stream.return_value = [mock_doc1, mock_doc2]

        # Patch the import source (lazy import inside the function)
        with patch("agents.shared.firestore_utils.get_firestore_collection",
                   return_value=mock_col):
            results = fetch_existing_titles()

        assert len(results) == 2
        titles = {r["title"] for r in results}
        assert "PRISMA 2020 Statement" in titles

    def test_firestore_error_returns_empty_list(self):
        from agents.reconciliation.tools import fetch_existing_titles
        with patch("agents.shared.firestore_utils.get_firestore_collection",
                   side_effect=Exception("Firestore unavailable")):
            results = fetch_existing_titles()
        assert results == []
