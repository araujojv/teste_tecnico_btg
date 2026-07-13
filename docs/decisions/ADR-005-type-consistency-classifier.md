# ADR-005 - type_consistency consome a decisão do classificador

## Status

Accepted

## Contexto

Comparar `tipo_declarado_no_titulo` (string livre, ex. "Bonificação em Ações")
com `tipo_evento` (enum `bonificacao`) via substring/casefold gerava
**falsos warnings** (doc 08): acentos e redação do título não cabem em match
textual com o enum.

O classificador já lê o documento e emite `divergencia_titulo_conteudo`
depois do raciocínio (schema autoregressivo).

## Decisão

`TypeConsistencyValidator` usa **somente** `divergencia_titulo_conteudo`:

- `None` (classificação não rodou) -> not_applicable
- `True` -> warning (cita `raciocinio_classificacao`)
- `False` -> pass

Sem recomputar por string matching.

## Consequências

- Doc 03: divergência true -> warning + rebaixa confiança / human_review.
- Doc 08: divergência false -> pass em type_consistency (human_review vem
  do golden_records).
- A qualidade da flag depende do classificador; o código não "adivinha"
  divergência por heurística de título.
