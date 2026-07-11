"""Tests for GoldenRecordsRepository."""

from __future__ import annotations

from pathlib import Path

from repositories.golden_records import GoldenRecordsRepository, MatchMethod


def test_loads_all_records(repository: GoldenRecordsRepository) -> None:
    assert len(repository.records) == 12


def test_find_by_isin(repository: GoldenRecordsRepository) -> None:
    record = repository.find_by_isin("BRTIETACNOR3")
    assert record is not None
    assert record.ticker == "TIET3"
    assert "Tiete" in record.emissor or "Tiet" in record.emissor


def test_find_by_ticker(repository: GoldenRecordsRepository) -> None:
    record = repository.find_by_ticker("BMRD4")
    assert record is not None
    assert record.isin == "BRBMRDACNPR7"


def test_find_by_cnpj_normalized(repository: GoldenRecordsRepository) -> None:
    record = repository.find_by_cnpj("76543210000112")
    assert record is not None
    assert record.ticker == "CSPR3"

    record_formatted = repository.find_by_cnpj("76.543.210/0001-12")
    assert record_formatted is not None
    assert record_formatted.isin == "BRCSPRACNOR1"


def test_find_by_nome_fuzzy(repository: GoldenRecordsRepository) -> None:
    match = repository.find_by_nome_fuzzy("Energetica Vale do Tiete S.A.")
    assert match is not None
    assert match.method == MatchMethod.NOME_FUZZY
    assert match.score >= 0.85
    assert match.record.ticker == "TIET3"


def test_emissor_match_case_and_accents(repository: GoldenRecordsRepository) -> None:
    """Literal ALL-CAPS from PDF must match title-case golden emissor."""
    # ENERGETICA VALE DO TIETE S.A. with accents (as extracted from doc 01)
    extracted = "ENERG\u00c9TICA VALE DO TIET\u00ca S.A."
    golden = "Energ\u00e9tica Vale do Tiet\u00ea S.A."
    match = repository.find_by_nome_fuzzy(extracted)
    assert match is not None
    assert match.record.ticker == "TIET3"
    assert match.score == 1.0
    # Sanity: normalized forms are equal
    from repositories.golden_records import normalize_text

    assert normalize_text(extracted) == normalize_text(golden)


def test_match_precedence_isin_over_ticker(
    repository: GoldenRecordsRepository,
) -> None:
    # ISIN of TIET3 with ticker of another issuer -> ISIN wins
    match = repository.match(isin="BRTIETACNOR3", ticker="BMRD4")
    assert match is not None
    assert match.method == MatchMethod.ISIN
    assert match.record.ticker == "TIET3"


def test_match_miss_horizonte(repository: GoldenRecordsRepository) -> None:
    match = repository.match(
        isin="BRCNHZACNOR5",
        ticker="CNHZ3",
        emissor="Construtora Horizonte S.A.",
    )
    assert match is None


def test_csv_path_with_space(golden_csv_path: Path) -> None:
    assert " " in golden_csv_path.name
    repo = GoldenRecordsRepository(golden_csv_path)
    assert len(repo.records) == 12
