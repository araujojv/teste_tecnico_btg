"""Golden records repository - CSV implementation (Repository pattern)."""

from __future__ import annotations

import csv
import re
import unicodedata
from difflib import SequenceMatcher
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class MatchMethod(str, Enum):
    ISIN = "isin"
    TICKER = "ticker"
    CNPJ = "cnpj"
    NOME_FUZZY = "nome_fuzzy"


class GoldenRecord(BaseModel):
    emissor: str
    cnpj: str
    isin: str
    ticker: str
    classe: str
    segmento_listagem: str
    status: str


class GoldenMatch(BaseModel):
    record: GoldenRecord
    method: MatchMethod
    score: float = Field(ge=0.0, le=1.0)


def normalize_cnpj(cnpj: str | None) -> str | None:
    if cnpj is None:
        return None
    digits = re.sub(r"\D", "", cnpj)
    return digits or None


def normalize_text(text: str | None) -> str | None:
    """Casefold + strip/collapse spaces + accent-insensitive (NFKD)."""
    if text is None:
        return None
    stripped = text.strip()
    if not stripped:
        return None
    # NFKD then drop combining marks so accented letters match base letters.
    decomposed = unicodedata.normalize("NFKD", stripped)
    without_accents = "".join(
        ch for ch in decomposed if not unicodedata.combining(ch)
    )
    cleaned = re.sub(r"\s+", " ", without_accents.casefold())
    return cleaned or None


class GoldenRecordsRepository:
    """Loads and queries the issuer reference base."""

    FUZZY_THRESHOLD = 0.85

    def __init__(self, csv_path: Path | str) -> None:
        self._path = Path(csv_path)
        self._records: list[GoldenRecord] = []
        self._by_isin: dict[str, GoldenRecord] = {}
        self._by_ticker: dict[str, GoldenRecord] = {}
        self._by_cnpj: dict[str, GoldenRecord] = {}
        self._load()

    def _load(self) -> None:
        with self._path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                record = GoldenRecord.model_validate(
                    {
                        "emissor": row["emissor"].strip(),
                        "cnpj": row["cnpj"].strip(),
                        "isin": row["isin"].strip().upper(),
                        "ticker": row["ticker"].strip().upper(),
                        "classe": row["classe"].strip(),
                        "segmento_listagem": row["segmento_listagem"].strip(),
                        "status": row["status"].strip(),
                    }
                )
                self._records.append(record)
                self._by_isin[record.isin] = record
                self._by_ticker[record.ticker] = record
                cnpj_key = normalize_cnpj(record.cnpj)
                if cnpj_key:
                    self._by_cnpj[cnpj_key] = record

    @property
    def records(self) -> list[GoldenRecord]:
        return list(self._records)

    def find_by_isin(self, isin: str | None) -> GoldenRecord | None:
        if not isin:
            return None
        return self._by_isin.get(isin.strip().upper())

    def find_by_ticker(self, ticker: str | None) -> GoldenRecord | None:
        if not ticker:
            return None
        return self._by_ticker.get(ticker.strip().upper())

    def find_by_cnpj(self, cnpj: str | None) -> GoldenRecord | None:
        key = normalize_cnpj(cnpj)
        if not key:
            return None
        return self._by_cnpj.get(key)

    def find_by_nome_fuzzy(
        self, nome: str | None, threshold: float | None = None
    ) -> GoldenMatch | None:
        needle = normalize_text(nome)
        if not needle:
            return None
        min_score = threshold if threshold is not None else self.FUZZY_THRESHOLD
        best: GoldenMatch | None = None
        for record in self._records:
            candidate = normalize_text(record.emissor)
            if not candidate:
                continue
            score = SequenceMatcher(None, needle, candidate).ratio()
            if score >= min_score and (best is None or score > best.score):
                best = GoldenMatch(
                    record=record,
                    method=MatchMethod.NOME_FUZZY,
                    score=score,
                )
        return best

    def match(
        self,
        *,
        isin: str | None = None,
        ticker: str | None = None,
        cnpj: str | None = None,
        emissor: str | None = None,
    ) -> GoldenMatch | None:
        """Precedence: ISIN -> ticker -> CNPJ -> fuzzy name."""
        by_isin = self.find_by_isin(isin)
        if by_isin is not None:
            return GoldenMatch(record=by_isin, method=MatchMethod.ISIN, score=1.0)

        by_ticker = self.find_by_ticker(ticker)
        if by_ticker is not None:
            return GoldenMatch(record=by_ticker, method=MatchMethod.TICKER, score=1.0)

        by_cnpj = self.find_by_cnpj(cnpj)
        if by_cnpj is not None:
            return GoldenMatch(record=by_cnpj, method=MatchMethod.CNPJ, score=1.0)

        return self.find_by_nome_fuzzy(emissor)
