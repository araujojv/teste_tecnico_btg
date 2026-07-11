"""Tests for type_consistency validator."""

from __future__ import annotations

from schemas.records import CorporateEventRecord, EventType, ValidationStatus
from validation.rules.type_consistency import TypeConsistencyValidator


def test_warning_when_divergencia_true(
    jcp_doc03_record: CorporateEventRecord,
) -> None:
    record = jcp_doc03_record.model_copy(
        update={
            "raciocinio_classificacao": (
                "Titulo fala em dividendos, mas o corpo descreve JCP "
                "(TJLP, IRRF 17,5%)."
            ),
        }
    )
    result = TypeConsistencyValidator().validate(record)
    assert result.status == ValidationStatus.WARNING
    assert result.details is not None
    assert result.details["rebaixar_confianca"] is True
    assert "JCP" in result.message or "jcp" in result.message.casefold()


def test_pass_when_divergencia_false_free_title() -> None:
    """Free-text title vs enum must not trigger string mismatch."""
    # "Bonificacao em Acoes" with accents via unicode escapes (Windows-safe).
    title = "Bonifica\u00e7\u00e3o em A\u00e7\u00f5es"
    record = CorporateEventRecord(
        tipo_evento=EventType.BONIFICACAO,
        tipo_declarado_no_titulo=title,
        divergencia_titulo_conteudo=False,
        raciocinio_classificacao="Conteudo e titulo apontam para bonificacao.",
    )
    result = TypeConsistencyValidator().validate(record)
    assert result.status == ValidationStatus.PASS


def test_pass_aligned_types() -> None:
    record = CorporateEventRecord(
        tipo_evento=EventType.DIVIDENDO,
        tipo_declarado_no_titulo="dividendo",
        divergencia_titulo_conteudo=False,
    )
    result = TypeConsistencyValidator().validate(record)
    assert result.status == ValidationStatus.PASS


def test_warning_flag_even_if_types_look_aligned() -> None:
    record = CorporateEventRecord(
        tipo_evento=EventType.JCP,
        tipo_declarado_no_titulo="jcp",
        divergencia_titulo_conteudo=True,
        raciocinio_classificacao="Flag de divergencia setada pelo classificador.",
    )
    result = TypeConsistencyValidator().validate(record)
    assert result.status == ValidationStatus.WARNING
    assert "Flag de divergencia" in result.message


def test_not_applicable_when_classification_not_run() -> None:
    record = CorporateEventRecord(
        tipo_evento=EventType.DIVIDENDO,
        tipo_declarado_no_titulo="Pagamento de Dividendos",
        divergencia_titulo_conteudo=None,
    )
    result = TypeConsistencyValidator().validate(record)
    assert result.status == ValidationStatus.NOT_APPLICABLE
