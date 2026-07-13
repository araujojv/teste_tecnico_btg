# ADR-003 - Structured outputs strict e schema intermediário

## Status

Accepted

## Contexto

Extração e classificação precisam de JSON estável para mapear para
`CorporateEventRecord` (Decimal, date, enums). Respostas livres da LLM
quebram o pipeline e a auditoria.

## Decisão

- Usar `client.beta.chat.completions.parse()` com modelo Pydantic e schema
  strict (`response_format` / structured outputs).
- Schema intermediário de extração (`ExtractionLLMOutput` / `ExtractedField`)
  com valores como string; o mapper em `extract.py` converte para
  `date` / `Decimal` / `EventType`.
- Classificação com schema autoregressivo: evidências -> raciocínio ->
  título -> tipo_evento -> divergência (AGENTS.md).

## Consequências

- Falhas de parse falham cedo (melhor que inventar campos).
- Prompt e schema ficam alinhados; mudanças de contrato exigem atualizar
  Pydantic + testes.
- Não validar com LLM o que o código valida depois.
