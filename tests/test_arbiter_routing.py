"""
Deterministic arbiter routing tests — required by docs/EVAL.md.
"arbiter routing given fixed inputs"

Routing logic (docs/SCHEMA.md + agents/prompts/arbiter.md):
  skip_reason set                                                → auto_exclude
  classification_confidence >= 0.8 AND relevance_score >= 0.6
    AND quality_score >= 80 AND ai_confidence >= 70
    AND panel_agreement >= 0.7                                   → auto_accept
  classification_confidence >= 0.8 AND relevance_score < 0.3    → auto_exclude
  quality_score < 60                                             → auto_exclude
  otherwise                                                      → review_needed
"""
import pytest


class TestComputeRoutingDecision:

    def test_auto_accept_high_quality_and_confidence(self):
        """Ideal resource: high quality, confidence, relevance, panel agreement."""
        from agents.arbiter.tools import compute_routing_decision
        decision = compute_routing_decision(
            relevance_score=0.9,
            classification_confidence=0.85,
            quality_score=88,
            ai_confidence=82,
            panel_agreement=0.85,
            skip_reason=None,
        )
        assert decision["routing"] == "auto_accept"

    def test_auto_accept_at_exact_thresholds(self):
        """At-threshold values must still route to auto_accept."""
        from agents.arbiter.tools import compute_routing_decision
        decision = compute_routing_decision(
            relevance_score=0.6,
            classification_confidence=0.8,
            quality_score=80,
            ai_confidence=70,
            panel_agreement=0.7,
            skip_reason=None,
        )
        assert decision["routing"] == "auto_accept"

    def test_review_needed_borderline_quality(self):
        """quality_score 60-79 → review_needed regardless of other signals."""
        from agents.arbiter.tools import compute_routing_decision
        decision = compute_routing_decision(
            relevance_score=0.9,
            classification_confidence=0.9,
            quality_score=72,
            ai_confidence=80,
            panel_agreement=0.9,
            skip_reason=None,
        )
        assert decision["routing"] == "review_needed"

    def test_review_needed_low_ai_confidence(self):
        """ai_confidence < 70 → review_needed regardless of quality_score."""
        from agents.arbiter.tools import compute_routing_decision
        decision = compute_routing_decision(
            relevance_score=0.9,
            classification_confidence=0.9,
            quality_score=85,
            ai_confidence=65,
            panel_agreement=0.9,
            skip_reason=None,
        )
        assert decision["routing"] == "review_needed"

    def test_review_needed_low_classification_confidence(self):
        """classification_confidence < 0.5 → review_needed."""
        from agents.arbiter.tools import compute_routing_decision
        decision = compute_routing_decision(
            relevance_score=0.7,
            classification_confidence=0.45,
            quality_score=82,
            ai_confidence=75,
            panel_agreement=0.8,
            skip_reason=None,
        )
        assert decision["routing"] == "review_needed"

    def test_review_needed_no_mvp_methodology(self):
        """Outside MVP methodologies: high quality still routes to human review."""
        from agents.arbiter.tools import compute_routing_decision
        decision = compute_routing_decision(
            relevance_score=0.85,
            classification_confidence=0.85,
            quality_score=85,
            ai_confidence=80,
            panel_agreement=0.8,
            skip_reason=None,
            has_mvp_methodology=False,
        )
        assert decision["routing"] == "review_needed"
        assert "MVP methodologies" in decision["reason"]

    def test_review_needed_low_panel_agreement(self):
        """panel_agreement < 0.5 (high disagreement) → review_needed."""
        from agents.arbiter.tools import compute_routing_decision
        decision = compute_routing_decision(
            relevance_score=0.85,
            classification_confidence=0.85,
            quality_score=88,
            ai_confidence=80,
            panel_agreement=0.4,
            skip_reason=None,
        )
        assert decision["routing"] == "review_needed"

    def test_auto_exclude_skip_reason(self):
        """skip_reason set → auto_exclude regardless of other signals."""
        from agents.arbiter.tools import compute_routing_decision
        decision = compute_routing_decision(
            relevance_score=0.0,
            classification_confidence=0.9,
            quality_score=90,
            ai_confidence=90,
            panel_agreement=0.9,
            skip_reason="homepage — not a discrete citable resource",
        )
        assert decision["routing"] == "auto_exclude"

    def test_auto_exclude_low_relevance(self):
        """relevance_score < 0.3 with high confidence → auto_exclude."""
        from agents.arbiter.tools import compute_routing_decision
        decision = compute_routing_decision(
            relevance_score=0.15,
            classification_confidence=0.85,
            quality_score=85,
            ai_confidence=80,
            panel_agreement=0.8,
            skip_reason=None,
        )
        assert decision["routing"] == "auto_exclude"

    def test_auto_exclude_very_low_quality(self):
        """quality_score < 60 → auto_exclude."""
        from agents.arbiter.tools import compute_routing_decision
        decision = compute_routing_decision(
            relevance_score=0.7,
            classification_confidence=0.8,
            quality_score=45,
            ai_confidence=80,
            panel_agreement=0.8,
            skip_reason=None,
        )
        assert decision["routing"] == "auto_exclude"

    def test_decision_includes_reason(self):
        """Every routing decision must include a reason string."""
        from agents.arbiter.tools import compute_routing_decision
        decision = compute_routing_decision(
            relevance_score=0.9, classification_confidence=0.9,
            quality_score=88, ai_confidence=82, panel_agreement=0.85,
            skip_reason=None,
        )
        assert "reason" in decision
        assert isinstance(decision["reason"], str)
        assert len(decision["reason"]) > 0

    def test_decision_includes_composite_score(self):
        """Every decision must include a composite_score (0-100)."""
        from agents.arbiter.tools import compute_routing_decision
        decision = compute_routing_decision(
            relevance_score=0.9, classification_confidence=0.9,
            quality_score=88, ai_confidence=82, panel_agreement=0.85,
            skip_reason=None,
        )
        assert "composite_score" in decision
        assert 0 <= decision["composite_score"] <= 100


class TestComputePanelAgreement:

    def test_all_same_scores_perfect_agreement(self):
        from agents.arbiter.tools import compute_panel_agreement
        scores = [{"dimension": "relevance", "score": 80, "pass": True}] * 6
        agreement = compute_panel_agreement(scores)
        assert agreement == 1.0

    def test_mixed_pass_fail_low_agreement(self):
        from agents.arbiter.tools import compute_panel_agreement
        scores = [
            {"dimension": "relevance", "score": 90, "pass": True},
            {"dimension": "accuracy", "score": 40, "pass": False},
            {"dimension": "authority", "score": 85, "pass": True},
            {"dimension": "currency", "score": 30, "pass": False},
            {"dimension": "accessibility", "score": 80, "pass": True},
            {"dimension": "practical_utility", "score": 35, "pass": False},
        ]
        agreement = compute_panel_agreement(scores)
        assert 0.0 <= agreement <= 1.0
        assert agreement < 0.7  # mixed results = low agreement

    def test_empty_scores_returns_0(self):
        from agents.arbiter.tools import compute_panel_agreement
        assert compute_panel_agreement([]) == 0.0


class TestHITLQueueWrite:

    def test_write_review_queue_item_returns_doc_id(self):
        from agents.shared.hitl import write_review_queue_item
        from unittest.mock import MagicMock, patch

        mock_col = MagicMock()
        mock_ref = MagicMock()
        mock_ref.id = "review-doc-001"
        mock_col.add.return_value = (None, mock_ref)

        with patch("agents.shared.hitl.get_firestore_collection", return_value=mock_col):
            doc_id = write_review_queue_item(
                resource_code="strobe-2007",
                routing="review_needed",
                reason="ai_confidence=65 < 70 threshold",
                panel_result={"panel_agreement": 0.7},
                draft_record={"resource_code": "strobe-2007"},
            )
        assert doc_id == "review-doc-001"

    def test_review_queue_item_has_required_fields(self):
        from agents.shared.hitl import write_review_queue_item
        from unittest.mock import MagicMock, patch

        mock_col = MagicMock()
        mock_ref = MagicMock()
        mock_ref.id = "review-doc-002"
        mock_col.add.return_value = (None, mock_ref)

        with patch("agents.shared.hitl.get_firestore_collection", return_value=mock_col):
            write_review_queue_item(
                resource_code="test-resource",
                routing="review_needed",
                reason="test reason",
                panel_result={"panel_agreement": 0.6},
                draft_record={"resource_code": "test-resource"},
            )

        written = mock_col.add.call_args[0][0]
        assert written["resource_code"] == "test-resource"
        assert written["routing"] == "review_needed"
        assert written["reason"] == "test reason"
        assert "queued_at" in written
        assert "status" in written
        assert written["status"] == "pending"
