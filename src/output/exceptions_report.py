"""Consolidate batch exceptions into a Markdown report for operators."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from schemas.records import ConfidenceLevel, ValidationStatus


def _tipo_evento(payload: dict[str, Any]) -> str:
    record = payload.get("record") or {}
    block = record.get("tipo_evento") or {}
    value = block.get("value")
    return str(value) if value is not None else "-"


def _overall(payload: dict[str, Any]) -> str:
    processing = payload.get("processing") or {}
    overall = processing.get("overall_confidence")
    if overall is None:
        return "-"
    return f"{float(overall):.3f}"


def _route(payload: dict[str, Any]) -> str:
    routing = payload.get("routing") or {}
    decision = routing.get("decision")
    return str(decision) if decision else "-"


def _has_non_pass_validation(payload: dict[str, Any]) -> bool:
    for item in payload.get("validation") or []:
        status = item.get("status")
        if status in (
            ValidationStatus.FAIL.value,
            ValidationStatus.WARNING.value,
        ):
            return True
    return False


def _needs_detail_section(payload: dict[str, Any]) -> bool:
    if _route(payload) == "human_review":
        return True
    return _has_non_pass_validation(payload)


def _non_pass_validators(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in (payload.get("validation") or [])
        if item.get("status")
        not in (ValidationStatus.PASS.value, ValidationStatus.NOT_APPLICABLE.value)
    ]


def _low_confidence_fields(payload: dict[str, Any]) -> list[tuple[str, dict]]:
    low: list[tuple[str, dict]] = []
    for name, block in (payload.get("record") or {}).items():
        if not isinstance(block, dict):
            continue
        conf = block.get("confidence")
        if not conf:
            continue
        if conf.get("level") == ConfidenceLevel.LOW.value:
            low.append((name, conf))
    return low


def build_exceptions_report(payloads: list[dict[str, Any]]) -> str:
    """
    Markdown report: summary table + detail sections for human_review / warnings.
    """
    lines: list[str] = [
        "# Relatorio de Excecoes - Corporate Events Agent",
        "",
        f"Documentos processados: **{len(payloads)}**",
        "",
        "## Resumo",
        "",
        "| Doc | tipo_evento | rota | overall |",
        "|-----|-------------|------|---------|",
    ]

    for payload in payloads:
        doc_id = payload.get("doc_id", "?")
        lines.append(
            f"| `{doc_id}` | {_tipo_evento(payload)} | {_route(payload)} | "
            f"{_overall(payload)} |"
        )

    detail_payloads = [p for p in payloads if _needs_detail_section(p)]
    lines.extend(["", "## Detalhes (human_review ou warnings)", ""])

    if not detail_payloads:
        lines.append(
            "Nenhum documento com human_review ou validadores nao-pass."
        )
        lines.append("")
        return "\n".join(lines)

    for payload in detail_payloads:
        doc_id = payload.get("doc_id", "?")
        lines.append(f"### `{doc_id}`")
        lines.append("")
        lines.append(f"- **Rota:** `{_route(payload)}`")
        lines.append(f"- **tipo_evento:** `{_tipo_evento(payload)}`")
        lines.append(f"- **overall_confidence:** `{_overall(payload)}`")

        reasons = (payload.get("routing") or {}).get("reasons") or []
        if reasons:
            lines.append("- **Razoes de roteamento:**")
            for reason in reasons:
                lines.append(f"  - {reason}")
        else:
            lines.append("- **Razoes de roteamento:** (nenhuma)")

        non_pass = _non_pass_validators(payload)
        if non_pass:
            lines.append("- **Validadores nao-pass:**")
            for item in non_pass:
                rule = item.get("rule")
                status = item.get("status")
                message = item.get("message")
                lines.append(f"  - `{rule}` = **{status}** -- {message}")
        else:
            lines.append("- **Validadores nao-pass:** nenhum")

        low_fields = _low_confidence_fields(payload)
        if low_fields:
            lines.append("- **Campos com confianca low:**")
            for name, conf in low_fields:
                score = conf.get("score")
                just = conf.get("justification", "")
                lines.append(f"  - `{name}` (score={score}): {just}")
        else:
            lines.append("- **Campos com confianca low:** nenhum")

        lines.append("")

    return "\n".join(lines)


def write_exceptions_report(
    payloads: list[dict[str, Any]],
    path: Path | str,
) -> Path:
    """Write UTF-8 Markdown exceptions report."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_exceptions_report(payloads), encoding="utf-8")
    return out
