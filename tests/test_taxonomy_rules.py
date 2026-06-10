"""Type-aware methodology requirement rules."""
import pytest


class TestMethodologyRequiredForType:
    def test_article_requires_methodology(self):
        from agents.shared.taxonomy_rules import methodology_required_for_type
        assert methodology_required_for_type("article") is True

    @pytest.mark.parametrize("optional_type", [
        "software", "community", "funding", "dataset", "template", "visual_reference",
    ])
    def test_optional_types_do_not_require_methodology(self, optional_type):
        from agents.shared.taxonomy_rules import methodology_required_for_type
        assert methodology_required_for_type(optional_type) is False

    def test_unknown_type_defaults_to_required(self):
        from agents.shared.taxonomy_rules import methodology_required_for_type
        assert methodology_required_for_type("not_a_type") is True

    def test_none_type_defaults_to_required(self):
        from agents.shared.taxonomy_rules import methodology_required_for_type
        assert methodology_required_for_type(None) is True
