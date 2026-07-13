# ADR-008 - Modelo LLM como configuração (três knobs)

## Status

Accepted

## Contexto

Extração de texto, classificação e visão podem precisar de tiers diferentes.
Hardcodar o modelo no provider impede troca sem alterar código e mistura
responsabilidades.

## Decisão

Três variáveis em `.env` / `config/settings.py`, nunca literais no código
de chamada:

| Knob | Env | Uso |
|------|-----|-----|
| EXTRACTION_MODEL | EXTRACTION_MODEL | PDF nativo (texto) |
| CLASSIFICATION_MODEL | CLASSIFICATION_MODEL | Classificação com texto |
| VISION_MODEL | VISION_MODEL | Extração OCR + classificação scanned |

Default dos três: `gpt-5.4-mini`. Subir de tier só se o lote provar erro
sistemático (custo vs qualidade).

## Consequências

- Mesmo adapter `OpenAIProvider.parse(messages, model=...)`.
- `.env.example` documenta os knobs; `.env` não vai para o git.
- Avaliação A/B de modelo não exige branch de código.
