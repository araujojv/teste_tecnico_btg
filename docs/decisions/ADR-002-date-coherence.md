# ADR-002 - Coerência temporal de datas (date_coherence)

## Status

Accepted

## Contexto

Avisos B3/CVM publicam aprovação, data-com, data-ex e pagamento. A ordem
temporal é regra operacional; a validação é determinística (código, sem LLM).

No gabarito inicial, o doc 05 (Aurora Saneamento) estava no grupo "limpo"
(auto_approve). A primeira execução do lote mostrou datas incoerentes no PDF:

| Campo | Valor no PDF |
|-------|--------------|
| data_aprovacao | 01/06/2026 |
| data_pagamento | **10/07/2026** |
| data_com | 15/07/2026 |
| data_ex | 16/07/2026 |

A armadilha **não estava mapeada** previamente; foi detectada por
`date_coherence` (fail) e roteada para human_review.

## Decisão

Invariante em `DateCoherenceValidator`:

```
data_aprovacao <= data_com < data_ex <= data_pagamento
```

- Só compara datas presentes; `data_com < data_ex` é estrito.
- Pagamento ausente declarado (doc 04) -> warning, não fail.
- Fail em datas -> human_review (política de roteamento).

## Consequências

- Doc 05 no gabarito: date_coherence fail -> human_review.
- Não "corrige" o PDF: evidência literal permanece; operador revisa.
- Ver `src/validation/rules/date_coherence.py` e AGENTS.md (armadilhas).
