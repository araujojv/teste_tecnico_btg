"""Unit tests for exceptions_report (no LLM)."""

from __future__ import annotations

from output.exceptions_report import build_exceptions_report


def test_exceptions_report_summary_and_detail() -> None:
    payloads = [
        {
            "doc_id": "01_ok",
            "processing": {"overall_confidence": 0.91},
            "record": {
                "tipo_evento": {"value": "dividendo", "confidence": None},
            },
            "validation": [
                {"rule": "golden_records", "status": "pass", "message": "ok"},
            ],
            "routing": {"decision": "auto_approve", "reasons": []},
        },
        {
            "doc_id": "08_fail",
            "processing": {"overall_confidence": 0.72},
            "record": {
                "tipo_evento": {"value": "bonificacao", "confidence": None},
                "valor_bruto": {
                    "value": "1.0",
                    "confidence": {
                        "level": "low",
                        "score": 0.3,
                        "justification": "ocr low",
                    },
                },
            },
            "validation": [
                {
                    "rule": "golden_records",
                    "status": "fail",
                    "message": "unknown issuer",
                },
            ],
            "routing": {
                "decision": "human_review",
                "reasons": ["golden_records fail"],
            },
        },
    ]
    md = build_exceptions_report(payloads)
    assert "| `01_ok` | dividendo | auto_approve | 0.910 |" in md
    assert "| `08_fail` | bonificacao | human_review | 0.720 |" in md
    assert "### `08_fail`" in md
    assert "golden_records" in md
    assert "valor_bruto" in md
    assert "### `01_ok`" not in md
