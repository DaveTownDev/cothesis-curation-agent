"""QC panel aggregation must tolerate Gemini omitting/mis-typing a panelist score.

A raw r["score"] previously raised KeyError, crashing the panel node (and the
ADK eval) when the model returned a row without a numeric score.
"""
from agents.qc_panel.tools import aggregate_panel_results, _as_float


def test_missing_score_does_not_crash():
    results = [
        {"dimension": "relevance", "score": 80, "pass": True},
        {"dimension": "accuracy", "pass": False},          # no 'score'
        {"pass": True},                                     # no 'score' or 'dimension'
    ]
    out = aggregate_panel_results(results)
    assert out["panel_agreement"] == round(2 / 3, 3)
    assert "accuracy" in out["summary"]            # missing-dimension default doesn't break failures list
    assert isinstance(out["avg_score"], float)


def test_as_float_tolerates_format_variations():
    assert _as_float(85) == 85.0
    assert _as_float("85") == 85.0
    assert _as_float("85%") == 85.0
    assert _as_float(None) == 0.0
    assert _as_float("not a number") == 0.0
    assert _as_float(None, default=50.0) == 50.0


def test_empty_results_safe():
    out = aggregate_panel_results([])
    assert out["panel_agreement"] == 0.0
    assert out["overall_pass"] is False
