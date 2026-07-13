# ADR-005 - type_consistency consome a decisao do classificador

## Status

Accepted

## Contexto

Comparar `tipo_declarado_no_titulo` (string livre, ex. "Bonificacao em Acoes")
com `tipo_evento` (enum `bonificacao`) via substring/casefold gerava
**falsos warnings** (doc 08): acentos e redacao do titulo nao cabem em match
textual com o enum.

O classificador ja le o documento e emite `divergencia_titulo_conteudo`
depois do raciocinio (schema autoregressivo).

## Decisao

`TypeConsistencyValidator` usa **somente** `divergencia_titulo_conteudo`:

- `None` (classificacao nao rodou) -> not_applicable
- `True` -> warning (cita `raciocinio_classificacao`)
- `False` -> pass

Sem recomputar por string matching.

## Consequencias

- Doc 03: divergencia true -> warning + rebaixa confianca / human_review.
- Doc 08: divergencia false -> pass em type_consistency (human_review vem
  do golden_records).
- A qualidade da flag depende do classificador; o codigo nao "adivinha"
  divergencia por heuristica de titulo.
