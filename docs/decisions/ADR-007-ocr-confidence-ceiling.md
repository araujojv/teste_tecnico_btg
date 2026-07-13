# ADR-007 - Teto de confiança para extração OCR / multimodal

## Status

Accepted

## Contexto

PDF escaneado (doc 07) exige visão (`VISION_MODEL`). OCR/visão é mais
propenso a erro de leitura; tratar confiança como nativa (base 0.90)
subestimaria risco operacional.

Multimodal só quando densidade de texto < limiar (custo); nativos nunca
passam pela rota de imagem.

## Decisão

- Scorer: base **0.70** para `method=ocr` ou `pdf_kind=scanned` (vs 0.90 native).
- HIGH exige score >= 0.8; com base OCR, valor/data tipicamente ficam em
  medium (~0.75) mesmo com validator pass.
- Roteamento: scanned com `overall_confidence < 0.85` -> human_review.

Sem OCR local (Tesseract etc.): a "OCR" é a LLM de visão já usada no
structured output - evita dependência extra e segundo motor de texto.

## Consequências

- Doc 07: human_review por teto OCR (overall ~0.74), mesmo com validadores
  em geral pass.
- Operador sabe que campos vieram de imagem (`FieldEvidence.method=ocr`).
