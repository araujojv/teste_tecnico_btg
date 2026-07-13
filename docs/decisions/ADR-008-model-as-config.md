# ADR-008 - Modelo LLM como configuracao (tres knobs)

## Status

Accepted

## Contexto

Extracao de texto, classificacao e visao podem precisar de tiers diferentes.
Hardcodar o modelo no provider impede troca sem alterar codigo e mistura
responsabilidades.

## Decisao

Tres variaveis em `.env` / `config/settings.py`, nunca literais no codigo
de chamada:

| Knob | Env | Uso |
|------|-----|-----|
| EXTRACTION_MODEL | EXTRACTION_MODEL | PDF nativo (texto) |
| CLASSIFICATION_MODEL | CLASSIFICATION_MODEL | Classificacao com texto |
| VISION_MODEL | VISION_MODEL | Extracao OCR + classificacao scanned |

Default dos tres: `gpt-5.4-mini`. Subir de tier so se o lote provar erro
sistematico (custo vs qualidade).

## Consequencias

- Mesmo adapter `OpenAIProvider.parse(messages, model=...)`.
- `.env.example` documenta os knobs; `.env` nao vai para o git.
- Avaliacao A/B de modelo nao exige branch de codigo.
