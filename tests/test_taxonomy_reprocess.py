"""Tests for taxonomy normalization on stored records."""
from agents.shared.taxonomy_reprocess import (
    reprocess_discipline_codes,
    reprocess_methodology_codes,
    reprocess_record_fields,
)


def test_legacy_methodology_mapped():
    assert reprocess_methodology_codes(["RS-01"]) == ["SYN-01"]
    assert reprocess_methodology_codes(["OD-06", "SYN-02"]) == ["EVAL-01", "SYN-02"]


def test_invalid_methodology_dropped():
    assert reprocess_methodology_codes(["RS-99", "NOT-A-CODE"]) == []


def test_discipline_slug_normalized():
    codes = reprocess_discipline_codes(["Cardiology", " adult-psychiatry "])
    assert "cardiology" in codes
    assert "adult-psychiatry" in codes


def test_record_patch_only_when_changed():
    patch = reprocess_record_fields({
        "methodology_codes": ["SYN-01"],
        "discipline_codes": ["cardiology"],
    })
    assert patch == {}

    patch = reprocess_record_fields({
        "methodology_codes": ["RS-04"],
        "discipline_codes": ["invalid-specialty", "cardiology"],
    })
    assert patch["methodology_codes"] == ["SYN-02"]
    assert patch["discipline_codes"] == ["cardiology"]
