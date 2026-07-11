"""Native extraction: LLM structured output -> CorporateEventRecord + evidence."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from config.settings import Settings, get_settings
from extraction.prompts import EXTRACTION_SYSTEM, build_extraction_user_prompt
from extraction.schemas import ExtractedField, ExtractionLLMOutput
from llm.openai_provider import get_llm_provider
from llm.provider import LLMProvider
from pipeline.state import DocumentState, PdfKind, append_audit
from schemas.records import (
    CorporateEventRecord,
    EventType,
    ExtractionMethod,
    FieldEvidence,
)

_DATE_PATTERNS = (
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y-%m-%d",
)

_EVENT_TYPE_ALIASES = {
    "dividendo": EventType.DIVIDENDO,
    "dividendos": EventType.DIVIDENDO,
    "jcp": EventType.JCP,
    "juros sobre capital proprio": EventType.JCP,
    "juros sobre o capital proprio": EventType.JCP,
    "bonificacao": EventType.BONIFICACAO,
    "grupamento": EventType.GRUPAMENTO,
}


def find_page(snippet: str | None, page_texts: list[str]) -> int | None:
    """Return 1-based page index where snippet occurs; None if not found."""
    if not snippet or not snippet.strip():
        return None
    needle = snippet.casefold()
    for index, text in enumerate(page_texts, start=1):
        if needle in text.casefold():
            return index
    # Fallback: try a shortened core of the snippet
    core = " ".join(snippet.split())
    if len(core) > 40:
        core = core[:40]
    core_cf = core.casefold()
    for index, text in enumerate(page_texts, start=1):
        if core_cf and core_cf in text.casefold():
            return index
    return None


def parse_brazilian_date(raw: str | None) -> date | None:
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    for fmt in _DATE_PATTERNS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_decimal(raw: str | None) -> Decimal | None:
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    cleaned = (
        text.replace("R$", "")
        .replace("%", "")
        .replace(" ", "")
        .strip()
    )
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _strip_accents(text: str) -> str:
    # Explicit unicode escapes to keep file ASCII-safe on Windows tooling.
    table = {
        "\u00e1": "a",
        "\u00e0": "a",
        "\u00e3": "a",
        "\u00e2": "a",
        "\u00e9": "e",
        "\u00ea": "e",
        "\u00ed": "i",
        "\u00f3": "o",
        "\u00f4": "o",
        "\u00f5": "o",
        "\u00fa": "u",
        "\u00e7": "c",
    }
    return "".join(table.get(ch, ch) for ch in text)


def parse_event_type(raw: str | None) -> EventType | None:
    if raw is None:
        return None
    key = re.sub(r"\s+", " ", raw.strip().casefold())
    key_ascii = _strip_accents(key)
    return _EVENT_TYPE_ALIASES.get(key) or _EVENT_TYPE_ALIASES.get(key_ascii)


def _evidence_for(
    field: ExtractedField,
    *,
    typed_value: Any,
    page_texts: list[str],
) -> FieldEvidence[Any] | None:
    if typed_value is None and (field.value is None or field.value.strip() == ""):
        return None
    return FieldEvidence(
        value=typed_value if typed_value is not None else field.value,
        snippet=field.snippet,
        page=find_page(field.snippet, page_texts),
        method=ExtractionMethod.NATIVE,
    )


def to_corporate_event_record(
    llm_out: ExtractionLLMOutput,
    page_texts: list[str],
) -> CorporateEventRecord:
    """Map LLM output to CorporateEventRecord with FieldEvidence + page."""
    emissor = llm_out.emissor.value
    cnpj = llm_out.cnpj.value
    isin = llm_out.isin.value.strip().upper() if llm_out.isin.value else None
    ticker = llm_out.ticker.value.strip().upper() if llm_out.ticker.value else None
    tipo_evento = parse_event_type(llm_out.tipo_evento.value)
    tipo_declarado_no_titulo = llm_out.tipo_declarado_no_titulo.value
    data_aprovacao = parse_brazilian_date(llm_out.data_aprovacao.value)
    data_com = parse_brazilian_date(llm_out.data_com.value)
    data_ex = parse_brazilian_date(llm_out.data_ex.value)
    data_pagamento = parse_brazilian_date(llm_out.data_pagamento.value)
    valor_bruto = parse_decimal(llm_out.valor_bruto.value)
    valor_liquido = parse_decimal(llm_out.valor_liquido.value)
    aliquota_ir = parse_decimal(llm_out.aliquota_ir.value)
    proporcao = llm_out.proporcao.value
    moeda = llm_out.moeda.value

    evidencias: dict[str, FieldEvidence[Any]] = {}
    mapping: list[tuple[str, ExtractedField, Any]] = [
        ("emissor", llm_out.emissor, emissor),
        ("cnpj", llm_out.cnpj, cnpj),
        ("isin", llm_out.isin, isin),
        ("ticker", llm_out.ticker, ticker),
        ("tipo_evento", llm_out.tipo_evento, tipo_evento),
        ("tipo_declarado_no_titulo", llm_out.tipo_declarado_no_titulo, tipo_declarado_no_titulo),
        ("data_aprovacao", llm_out.data_aprovacao, data_aprovacao),
        ("data_com", llm_out.data_com, data_com),
        ("data_ex", llm_out.data_ex, data_ex),
        ("data_pagamento", llm_out.data_pagamento, data_pagamento),
        ("valor_bruto", llm_out.valor_bruto, valor_bruto),
        ("valor_liquido", llm_out.valor_liquido, valor_liquido),
        ("aliquota_ir", llm_out.aliquota_ir, aliquota_ir),
        ("proporcao", llm_out.proporcao, proporcao),
        ("moeda", llm_out.moeda, moeda),
    ]
    for name, field, typed in mapping:
        ev = _evidence_for(field, typed_value=typed, page_texts=page_texts)
        if ev is not None:
            evidencias[name] = ev

    return CorporateEventRecord(
        emissor=emissor,
        cnpj=cnpj,
        isin=isin,
        ticker=ticker,
        tipo_evento=tipo_evento,
        tipo_declarado_no_titulo=tipo_declarado_no_titulo,
        data_aprovacao=data_aprovacao,
        data_com=data_com,
        data_ex=data_ex,
        data_pagamento=data_pagamento,
        data_pagamento_ausente_declarada=llm_out.data_pagamento_ausente_declarada,
        valor_bruto=valor_bruto,
        valor_liquido=valor_liquido,
        aliquota_ir=aliquota_ir,
        proporcao=proporcao,
        moeda=moeda,
        evidencias=evidencias,
    )


def extract_native(
    state: DocumentState,
    provider: LLMProvider | None = None,
    settings: Settings | None = None,
) -> DocumentState:
    """Fill state.record from native PDF text via structured LLM output."""
    if state.pdf_kind != PdfKind.NATIVE:
        raise ValueError(
            f"extract_native requires pdf_kind=native, got {state.pdf_kind}"
        )
    cfg = settings or get_settings()
    llm = provider or get_llm_provider(cfg)

    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM},
        {
            "role": "user",
            "content": build_extraction_user_prompt(state.page_texts),
        },
    ]
    llm_out = llm.parse(
        messages,
        ExtractionLLMOutput,
        model=cfg.extraction_model,
    )
    record = to_corporate_event_record(llm_out, state.page_texts)
    filled = [
        name
        for name in (
            "emissor",
            "cnpj",
            "isin",
            "ticker",
            "tipo_evento",
            "tipo_declarado_no_titulo",
            "data_aprovacao",
            "data_com",
            "data_ex",
            "data_pagamento",
            "valor_bruto",
            "valor_liquido",
            "aliquota_ir",
            "proporcao",
            "moeda",
        )
        if getattr(record, name) is not None
    ]
    updated = state.model_copy(update={"record": record})
    return append_audit(
        updated,
        (
            f"extract_native: model={cfg.extraction_model}, "
            f"fields={filled}, evidencias={len(record.evidencias)}"
        ),
    )
