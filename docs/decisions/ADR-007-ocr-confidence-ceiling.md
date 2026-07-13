# ADR-007 - Teto de confianca para extracao OCR / multimodal

## Status

Accepted

## Contexto

PDF escaneado (doc 07) exige visao (`VISION_MODEL`). OCR/visao e mais
propenso a erro de leitura; tratar confianca como nativa (base 0.90)
subestimaria risco operacional.

Multimodal so quando densidade de texto < limiar (custo); nativos nunca
passam pela rota de imagem.

## Decisao

- Scorer: base **0.70** para `method=ocr` ou `pdf_kind=scanned` (vs 0.90 native).
- HIGH exige score >= 0.8; com base OCR, valor/data tipicamente ficam em
  medium (~0.75) mesmo com validator pass.
- Roteamento: scanned com `overall_confidence < 0.85` -> human_review.

Sem OCR local (Tesseract etc.): a "OCR" e a LLM de visao ja usada no
structured output — evita dependencia extra e segundo motor de texto.

## Consequencias

- Doc 07: human_review por teto OCR (overall ~0.74), mesmo com validadores
  em geral pass.
- Operador sabe que campos vieram de imagem (`FieldEvidence.method=ocr`).
