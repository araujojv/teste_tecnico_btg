# ADR-004 - golden_records prevalece sobre checksum ISIN

## Status

Accepted

## Contexto

ISINs do lote de teste são fictícios: muitos falham no dígito verificador
ISO 6166 / Luhn, mas existem no `golden_records.csv`. Tratar checksum fail
como hard-fail derrubaria docs válidos na base de referência (ex.: doc 01)
para human_review sem necessidade operacional.

## Decisão

Em `isin_checksum`:

- Checksum inválido **e** ISIN confirmado no golden_records -> **warning**
  (não fail), com `details.confirmed_in_golden_records=true`.
- Checksum inválido **e** ausente do golden -> **fail**.
- Scorer não aplica penalidade -0.20 nesse warning quando golden confirmou.

Hierarquia: match de emissor/ISIN na base de referência > pureza do checksum
em lote sintético.

## Consequências

- Docs 01-07 com ISIN no golden passam no roteamento apesar do checksum.
- Doc 08 (emissor inexistente) continua fail em golden_records e checksum.
- Em produção com ISINs reais, o warning diminui; a regra permanece segura.
