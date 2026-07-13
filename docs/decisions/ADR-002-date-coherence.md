# ADR-002 - Coerencia temporal de datas (date_coherence)

## Status

Accepted

## Contexto

Avisos B3/CVM publicam aprovacao, data-com, data-ex e pagamento. A ordem
temporal e regra operacional; a validacao e deterministica (codigo, sem LLM).

No gabarito inicial, o doc 05 (Aurora Saneamento) estava no grupo "limpo"
(auto_approve). A primeira execucao do lote mostrou datas incoerentes no PDF:

| Campo | Valor no PDF |
|-------|--------------|
| data_aprovacao | 01/06/2026 |
| data_pagamento | **10/07/2026** |
| data_com | 15/07/2026 |
| data_ex | 16/07/2026 |

A armadilha **nao estava mapeada** previamente; foi detectada por
`date_coherence` (fail) e roteada para human_review.

## Decisao

Invariante em `DateCoherenceValidator`:

```
data_aprovacao <= data_com < data_ex <= data_pagamento
```

- So compara datas presentes; `data_com < data_ex` e estrito.
- Pagamento ausente declarado (doc 04) -> warning, nao fail.
- Fail em datas -> human_review (politica de roteamento).

## Consequencias

- Doc 05 no gabarito: date_coherence fail -> human_review.
- Nao "corrige" o PDF: evidencia literal permanece; operador revisa.
- Ver `src/validation/rules/date_coherence.py` e AGENTS.md (armadilhas).
