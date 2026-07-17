"""Regression tests for the robust panel decision parser (P0 fix).

The OLD parser silently defaulted any response whose JSON failed `json.loads`
(literal control chars / newlines in reasoning, ```json fences, nested braces)
to decision=0, confidence=0.5 — systematically biasing axis-1 over-dispersion
and axis-2 over_reliance for verbose models (claude/gemini). The fix must:
  - recover the TRUE decision from fenced / control-char / nested-brace JSON,
  - fall back to regex when JSON is malformed but a 0/1 decision is present,
  - RAISE PanelParseError (never fabricate 0/0.5) when nothing is extractable.
"""

import json

import pytest

from twdf.panel.real_panel import (
    PanelParseError,
    _parse_decision_response,
    _parse_decision_with_confidence,
)


def test_control_char_bare_newline_recovers_true_decision():
    # Real failure mode: literal newline inside the reasoning string -> old json.loads
    # raised "Invalid control character" -> old parser returned (0, 0.5). Must recover 1/0.9.
    resp = '{\n  "decision": 1,\n  "confidence": 0.9,\n  "reasoning": "line one\nline two"\n}'
    with pytest.raises(json.JSONDecodeError):
        json.loads(resp)  # confirm strict json really fails on this
    d, c, _ = _parse_decision_with_confidence(resp)
    assert d == 1
    assert c == pytest.approx(0.9)


def test_markdown_json_fence_recovers():
    resp = '```json\n{"decision": 0, "confidence": 0.65, "reasoning": "neg"}\n```'
    d, c, _ = _parse_decision_with_confidence(resp)
    assert d == 0 and c == pytest.approx(0.65)


def test_nested_braces_in_reasoning_recovers():
    resp = '{"decision": 1, "confidence": 0.8, "reasoning": "the set {a,b} matters {x}"}'
    d, c, _ = _parse_decision_with_confidence(resp)
    assert d == 1 and c == pytest.approx(0.8)


def test_prose_prefix_then_json_recovers():
    resp = 'Let me think about this.\n\n```json\n{"decision": 1, "confidence": 0.7}\n```'
    d, c, _ = _parse_decision_with_confidence(resp)
    assert d == 1 and c == pytest.approx(0.7)


def test_regex_fallback_when_json_malformed():
    # Truncated / non-JSON but an explicit decision is present -> regex fallback recovers it.
    resp = 'decision: 1, confidence: 0.55 (model rambled without valid json'
    d, c, _ = _parse_decision_with_confidence(resp)
    assert d == 1 and c == pytest.approx(0.55)


def test_confidence_clamped():
    resp = '{"decision": 1, "confidence": 1.7}'
    d, c, _ = _parse_decision_with_confidence(resp)
    assert d == 1 and c == 1.0


def test_unparseable_raises_not_fabricates():
    resp = "I cannot answer this question with a clear yes or no at this time."
    with pytest.raises(PanelParseError):
        _parse_decision_with_confidence(resp)


def test_invalid_decision_value_raises():
    resp = '{"decision": 7, "confidence": 0.9}'
    with pytest.raises(PanelParseError):
        _parse_decision_with_confidence(resp)


def test_decision_only_parser_control_char_recovers():
    resp = '{\n  "decision": 1,\n  "reasoning": "multi\nline reasoning here"\n}'
    d, _ = _parse_decision_response(resp)
    assert d == 1


def test_decision_only_parser_unparseable_raises():
    with pytest.raises(PanelParseError):
        _parse_decision_response("no decision anywhere in this text")


def test_valid_clean_json_still_works():
    d, c, r = _parse_decision_with_confidence('{"decision": 0, "confidence": 0.5, "reasoning": "ok"}')
    assert d == 0 and c == 0.5 and r == "ok"
