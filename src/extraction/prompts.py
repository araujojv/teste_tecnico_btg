"""Prompts for native PDF field extraction (no classification reasoning here)."""

from __future__ import annotations


EXTRACTION_SYSTEM = """\
You extract structured fields from Brazilian corporate-event notices (B3/CVM).

Rules:
- Extract ONLY what is explicitly present in the document text.
- If a field is absent or unclear, set value=null and snippet=null. NEVER invent values.
- For each non-null value, set snippet to a short literal quote from the document that supports it.
- tipo_evento value must be one of: dividendo, jcp, bonificacao, grupamento (lowercase), or null.
- tipo_declarado_no_titulo: the event type as it appears LITERALLY in the notice title/header \
(e.g. "Pagamento de Dividendos", "Dividendos", "JCP"). Keep the wording from the title; \
set null ONLY if the title/header does not indicate an event type.
- Dates as dd/mm/yyyy when present (Brazilian format).
- Monetary amounts as decimal strings using '.' as separator (e.g. "0.4275"), without currency symbols.
- aliquota_ir as a FRACTION string, not percent: 10% -> "0.10"; 17.5% -> "0.175".
- aliquota_ir: fill ONLY when the rate explicitly applies to THIS notice's corporate event \
(the provento itself). If the text mentions IR/IRRF only as a general rule, threshold, \
exemption, or conditional withholding that is NOT the rate on this event's per-share amount, \
set aliquota_ir value=null and snippet=null.
- moeda: use "BRL" when amounts are in R$, else null if unknown.
- data_pagamento_ausente_declarada=true only when the document explicitly says payment date \
is undefined / will be defined later (e.g. "sera oportunamente definida"); otherwise false \
and leave data_pagamento null if missing.
- proporcao: only for bonificacao/grupamento ratios (e.g. "1:10"); otherwise null.
"""


def build_extraction_user_prompt(page_texts: list[str]) -> str:
    """Build user message with numbered pages for evidence grounding."""
    parts: list[str] = [
        "Extract all corporate-event fields from the following document pages.",
        "Return structured output matching the schema.",
        "",
    ]
    for index, text in enumerate(page_texts, start=1):
        parts.append(f"--- PAGE {index} ---")
        parts.append(text if text.strip() else "(no extractable text)")
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"
