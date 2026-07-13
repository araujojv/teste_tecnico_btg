# ADR-004 - golden_records prevalece sobre checksum ISIN

## Status

Accepted

## Contexto

ISINs do lote de teste sao ficticios: muitos falham no digito verificador
ISO 6166 / Luhn, mas existem no `golden_records.csv`. Tratar checksum fail
como hard-fail derrubaria docs validos na base de referencia (ex.: doc 01)
para human_review sem necessidade operacional.

## Decisao

Em `isin_checksum`:

- Checksum invalido **e** ISIN confirmado no golden_records -> **warning**
  (nao fail), com `details.confirmed_in_golden_records=true`.
- Checksum invalido **e** ausente do golden -> **fail**.
- Scorer nao aplica penalidade -0.20 nesse warning quando golden confirmou.

Hierarquia: match de emissor/ISIN na base de referencia > pureza do checksum
em lote sintetico.

## Consequencias

- Docs 01-07 com ISIN no golden passam no roteamento apesar do checksum.
- Doc 08 (emissor inexistente) continua fail em golden_records e checksum.
- Em producao com ISINs reais, o warning diminui; a regra permanece segura.
