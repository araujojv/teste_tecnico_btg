# Relatorio de Excecoes - Corporate Events Agent

Documentos processados: **8**

## Resumo

| Doc | tipo_evento | rota | overall |
|-----|-------------|------|---------|
| `01_energetica_vale_tiete_dividendo` | dividendo | auto_approve | 0.846 |
| `02_banco_meridional_jcp` | jcp | auto_approve | 0.929 |
| `03_siderurgica_paranaense_proventos` | jcp | human_review | 0.893 |
| `04_rede_varejo_jcp_sem_data` | jcp | auto_approve | 0.857 |
| `05_aurora_saneamento_dividendo_datas` | dividendo | human_review | 0.704 |
| `06_petroquimica_litoral_grupamento` | grupamento | auto_approve | 0.904 |
| `07_telecom_norte_jcp_SCAN` | jcp | human_review | 0.743 |
| `08_construtora_horizonte_bonificacao` | bonificacao | human_review | 0.729 |

## Detalhes (human_review ou warnings)

### `01_energetica_vale_tiete_dividendo`

- **Rota:** `auto_approve`
- **tipo_evento:** `dividendo`
- **overall_confidence:** `0.846`
- **Razoes de roteamento:**
  - auto_approve with warnings: gross_net_consistency, isin_checksum
- **Validadores nao-pass:**
  - `gross_net_consistency` = **warning** -- Missing fields for gross/net check: valor_liquido, aliquota_ir.
  - `isin_checksum` = **warning** -- ISIN checksum invalid (BRTIETACNOR3: digit=3, expected=0), but ISIN confirmed in golden_records reference base.
- **Campos com confianca low:**
  - `valor_liquido` (score=0.49999999999999994): valor_liquido: level=low, score=0.50. Signals: extraction_method=native (+0.90 base); field_absent (cap 0.70); validator:gross_net_consistency=warning (-0.20)
  - `aliquota_ir` (score=0.49999999999999994): aliquota_ir: level=low, score=0.50. Signals: extraction_method=native (+0.90 base); field_absent (cap 0.70); validator:gross_net_consistency=warning (-0.20)

### `02_banco_meridional_jcp`

- **Rota:** `auto_approve`
- **tipo_evento:** `jcp`
- **overall_confidence:** `0.929`
- **Razoes de roteamento:**
  - auto_approve with warnings: isin_checksum
- **Validadores nao-pass:**
  - `isin_checksum` = **warning** -- ISIN checksum invalid (BRBMRDACNPR7: digit=7, expected=3), but ISIN confirmed in golden_records reference base.
- **Campos com confianca low:** nenhum

### `03_siderurgica_paranaense_proventos`

- **Rota:** `human_review`
- **tipo_evento:** `jcp`
- **overall_confidence:** `0.893`
- **Razoes de roteamento:**
  - critical field 'tipo_evento' confidence=low (tipo_evento: level=low, score=0.45. Signals: extraction_method=native (+0.90 base); validator:type_consistency=warning (-0.20); divergencia_titulo_conteudo=true (-0.25))
- **Validadores nao-pass:**
  - `isin_checksum` = **warning** -- ISIN checksum invalid (BRCSPRACNOR1: digit=1, expected=5), but ISIN confirmed in golden_records reference base.
  - `type_consistency` = **warning** -- Title/content divergence flagged by classifier. Raciocinio: O título menciona distribuição de dividendos, mas o corpo do aviso descreve expressamente remuneração do capital próprio, limitada à TJLP pro rata die, com retenção de IRRF de 17,5% e imputação ao dividendo obrigatório. Esses são sinais determinísticos de JCP, não de dividendo. Portanto, a classificação deve seguir o conteúdo do documento.
- **Campos com confianca low:**
  - `tipo_evento` (score=0.44999999999999996): tipo_evento: level=low, score=0.45. Signals: extraction_method=native (+0.90 base); validator:type_consistency=warning (-0.20); divergencia_titulo_conteudo=true (-0.25)

### `04_rede_varejo_jcp_sem_data`

- **Rota:** `auto_approve`
- **tipo_evento:** `jcp`
- **overall_confidence:** `0.857`
- **Razoes de roteamento:**
  - auto_approve with warnings: date_coherence, isin_checksum
- **Validadores nao-pass:**
  - `date_coherence` = **warning** -- Payment date declared absent in the document (e.g. 'sera oportunamente definida').
  - `isin_checksum` = **warning** -- ISIN checksum invalid (BRRVBRACNOR9: digit=9, expected=7), but ISIN confirmed in golden_records reference base.
- **Campos com confianca low:** nenhum

### `05_aurora_saneamento_dividendo_datas`

- **Rota:** `human_review`
- **tipo_evento:** `dividendo`
- **overall_confidence:** `0.704`
- **Razoes de roteamento:**
  - fail date_coherence: Date incoherence: data_ex=2026-07-16 must be <= data_pagamento=2026-07-10.
- **Validadores nao-pass:**
  - `date_coherence` = **fail** -- Date incoherence: data_ex=2026-07-16 must be <= data_pagamento=2026-07-10.
  - `gross_net_consistency` = **warning** -- Missing fields for gross/net check: valor_liquido, aliquota_ir.
  - `isin_checksum` = **warning** -- ISIN checksum invalid (BRAURSACNOR4: digit=4, expected=9), but ISIN confirmed in golden_records reference base.
- **Campos com confianca low:**
  - `data_aprovacao` (score=0.45): data_aprovacao: level=low, score=0.45. Signals: extraction_method=native (+0.90 base); validator:date_coherence=fail (-0.45)
  - `data_com` (score=0.45): data_com: level=low, score=0.45. Signals: extraction_method=native (+0.90 base); validator:date_coherence=fail (-0.45)
  - `data_ex` (score=0.45): data_ex: level=low, score=0.45. Signals: extraction_method=native (+0.90 base); validator:date_coherence=fail (-0.45)
  - `data_pagamento` (score=0.45): data_pagamento: level=low, score=0.45. Signals: extraction_method=native (+0.90 base); validator:date_coherence=fail (-0.45)
  - `valor_liquido` (score=0.49999999999999994): valor_liquido: level=low, score=0.50. Signals: extraction_method=native (+0.90 base); field_absent (cap 0.70); validator:gross_net_consistency=warning (-0.20)
  - `aliquota_ir` (score=0.49999999999999994): aliquota_ir: level=low, score=0.50. Signals: extraction_method=native (+0.90 base); field_absent (cap 0.70); validator:gross_net_consistency=warning (-0.20)

### `06_petroquimica_litoral_grupamento`

- **Rota:** `auto_approve`
- **tipo_evento:** `grupamento`
- **overall_confidence:** `0.904`
- **Razoes de roteamento:**
  - auto_approve with warnings: isin_checksum
- **Validadores nao-pass:**
  - `isin_checksum` = **warning** -- ISIN checksum invalid (BRPQLTACNOR8: digit=8, expected=6), but ISIN confirmed in golden_records reference base.
- **Campos com confianca low:** nenhum

### `07_telecom_norte_jcp_SCAN`

- **Rota:** `human_review`
- **tipo_evento:** `jcp`
- **overall_confidence:** `0.743`
- **Razoes de roteamento:**
  - OCR/scanned document with overall_confidence=0.743 < 0.85
- **Validadores nao-pass:**
  - `isin_checksum` = **warning** -- ISIN checksum invalid (BRTLNRACNPR2: digit=2, expected=6), but ISIN confirmed in golden_records reference base.
- **Campos com confianca low:** nenhum

### `08_construtora_horizonte_bonificacao`

- **Rota:** `human_review`
- **tipo_evento:** `bonificacao`
- **overall_confidence:** `0.729`
- **Razoes de roteamento:**
  - fail golden_records: Issuer not found in reference base (isin=BRCNHZACNOR5, ticker=CNHZ3, cnpj=09.888.999/0001-21, emissor=CONSTRUTORA HORIZONTE S.A.).
- **Validadores nao-pass:**
  - `golden_records` = **fail** -- Issuer not found in reference base (isin=BRCNHZACNOR5, ticker=CNHZ3, cnpj=09.888.999/0001-21, emissor=CONSTRUTORA HORIZONTE S.A.).
  - `isin_checksum` = **fail** -- Invalid ISIN checksum: BRCNHZACNOR5 (digit=5, expected=6).
- **Campos com confianca low:**
  - `emissor` (score=0.45): emissor: level=low, score=0.45. Signals: extraction_method=native (+0.90 base); validator:golden_records=fail (-0.45)
  - `cnpj` (score=0.45): cnpj: level=low, score=0.45. Signals: extraction_method=native (+0.90 base); validator:golden_records=fail (-0.45)
  - `isin` (score=0.0): isin: level=low, score=0.00. Signals: extraction_method=native (+0.90 base); validator:golden_records=fail (-0.45); validator:isin_checksum=fail (-0.45)
  - `ticker` (score=0.45): ticker: level=low, score=0.45. Signals: extraction_method=native (+0.90 base); validator:golden_records=fail (-0.45)
