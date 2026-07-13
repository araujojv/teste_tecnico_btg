# ADR-003 - Structured outputs strict e schema intermediario

## Status

Accepted

## Contexto

Extracao e classificacao precisam de JSON estavel para mapear para
`CorporateEventRecord` (Decimal, date, enums). Respostas livres da LLM
quebram o pipeline e a auditoria.

## Decisao

- Usar `client.beta.chat.completions.parse()` com modelo Pydantic e schema
  strict (`response_format` / structured outputs).
- Schema intermediario de extracao (`ExtractionLLMOutput` / `ExtractedField`)
  com valores como string; o mapper em `extract.py` converte para
  `date` / `Decimal` / `EventType`.
- Classificacao com schema autoregressivo: evidencias -> raciocinio ->
  titulo -> tipo_evento -> divergencia (AGENTS.md).

## Consequencias

- Falhas de parse falham cedo (melhor que inventar campos).
- Prompt e schema ficam alinhados; mudancas de contrato exigem atualizar
  Pydantic + testes.
- Nao validar com LLM o que o codigo valida depois.
