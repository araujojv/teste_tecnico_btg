# CLAUDE.md — Case Técnico AI Developer (Asset Servicing)

## Contexto

Pipeline que processa avisos de eventos corporativos (PDFs no padrão B3/CVM) e produz, para cada documento, um registro estruturado, validado e auditável. Erros de extração aqui são erros financeiros/regulatórios: classificar errado o tipo de provento muda o tratamento tributário.

Entregáveis: código + README com trade-offs + 1 JSON por documento + relatório de exceções.
Haverá sessão técnica ao vivo (45 min) para estender e depurar o código — **priorizar simplicidade e legibilidade sobre abstração**.

## Decisões travadas (NÃO reavaliar, NÃO sugerir alternativas)

1. **Stack**: Python 3.11+ · Pydantic v2 · SDK OpenAI direto (structured outputs com `json_schema` + `strict: true`). **SEM LangGraph / LangChain / frameworks de agente** — o fluxo é um DAG linear com 2 branches, um `if` resolve (ADR-001).
2. **Pipeline como funções puras**: cada etapa é `(DocumentState) -> DocumentState`. Um orquestrador simples encadeia. Estado é Pydantic, com `audit_trail` append-only.
3. **Provider atrás de Adapter**: interface `LLMProvider` com implementação OpenAI. Troca de provider não toca no pipeline.
4. **Classificação atrás de interface** `EventClassifier`: hoje é LLM; em produção com volume seria classificador treinado (custo). Documentado como trade-off, não implementado (não há dataset — são 8 docs).
5. **Autoregressividade no schema**: no output de classificação, a ORDEM dos campos é obrigatória: `evidencias` → `raciocinio` → `tipo_declarado_no_titulo` → `tipo_evento` → `divergencia_titulo_conteudo`. A LLM gera o raciocínio ANTES de classificar.
6. **Multimodal só quando necessário**: PDFs nativos via pdfplumber (texto). Rota multimodal (página → imagem → LLM visão) SOMENTE para escaneados, detectados por densidade de texto abaixo de limiar. Motivo: custo.
7. **Validação determinística primeiro**: regras de coerência são código puro testável com pytest, sem LLM. LLM não valida — LLM extrai e classifica; código valida.
8. **Baixa confiança → humano, sem retry**: não fazer "retry até passar" — em contexto regulatório isso mascara incerteza. Rotear para revisão humana com justificativa.

## Armadilhas conhecidas do lote (gabarito esperado)

| Doc | Armadilha | Comportamento esperado |
|---|---|---|
| 01, 02, 06 | Nenhuma | Extração limpa → auto_approve |
| 03 | Título diz "Dividendos", conteúdo descreve JCP (limitado à TJLP, IRRF 17,5%, imputado ao dividendo obrigatório — art. 9º Lei 9.249/95) | `tipo_evento = jcp`, warning de divergência título/conteúdo → human_review |
| 04 | Data de pagamento "será oportunamente definida" (ausência declarada no doc) | Campo `null` + flag de ausência declarada → **warning, não fail** |
| 05 | Datas incoerentes no próprio aviso: `data_pagamento` 10/07/2026 anterior a `data_com` 15/07/2026 e `data_ex` 16/07/2026 | `date_coherence` = fail → human_review |
| 07 | PDF escaneado (sem texto extraível) | Rota multimodal; teto de confiança menor para campos via OCR |
| 08 | Emissor (Construtora Horizonte, CNHZ3, ISIN BRCNHZACNOR5) **não existe** no golden_records.csv | Validação `fail` → human_review obrigatório |

Sanity check matemático do doc 03: `0,09215 × (1 − 0,175) = 0,07602375` = valor líquido informado.

## Regras de validação (Chain of Responsibility)

Cada validador implementa `Validator.validate(record) -> ValidationResult` com status `pass | fail | warning | not_applicable`:

1. `golden_records` — match por ISIN, ticker, CNPJ e nome (fuzzy) via `GoldenRecordsRepository` (Repository pattern, impl CSV)
2. `date_coherence` — `aprovacao ≤ data_com < data_ex ≤ pagamento`; data ausente declarada = warning (ADR-002)
3. `gross_net_consistency` — `bruto × (1 − aliquota) ≈ liquido` (tolerância de arredondamento); `not_applicable` para grupamento/bonificação
4. `isin_checksum` — validação determinística do dígito verificador
5. `type_consistency` — declarado vs inferido; divergência = warning + rebaixa confiança

## Política de roteamento (ordem de precedência)

1. `fail` em golden_records → human_review
2. `fail` em datas ou bruto/líquido → human_review
3. Campo crítico (tipo_evento, valor, data_com) com confiança `low` → human_review
4. Doc via OCR com confiança geral < 0.85 → human_review
5. Caso contrário → auto_approve (warnings vão ao relatório mesmo assim)

## Rastreabilidade (requisito do case)

Todo campo extraído carrega `FieldEvidence`: valor + snippet literal do documento + página + método de extração. O operador deve auditar sem reabrir o PDF.

## Estrutura do projeto

```
corporate-events-agent/
├── CLAUDE.md
├── README.md                  # aponta para docs/decisions/
├── pyproject.toml
├── .env.example
├── config/settings.py         # Pydantic Settings
├── docs/
│   ├── decisions/             # ADRs numerados (ADR-001-sem-framework.md, ...)
│   ├── architecture/          # diagrama do fluxo de dados
│   └── schemas/               # contrato do JSON de saída + exemplo comentado
├── src/
│   ├── pipeline/
│   │   ├── state.py           # DocumentState (Pydantic)
│   │   ├── steps/             # ingest.py, extract.py, classify.py, validate.py, score.py, route.py
│   │   └── orchestrator.py    # encadeia os steps
│   ├── extraction/            # strategies: native.py, ocr.py + factory
│   ├── classification/        # EventClassifier (interface + impl LLM)
│   ├── validation/            # base.py + rules/
│   ├── repositories/          # golden_records.py
│   ├── llm/                   # provider.py (Adapter) + openai_provider.py
│   ├── confidence/            # scorer.py
│   ├── schemas/               # records.py
│   └── output/                # record_builder.py, exceptions_report.py
├── main.py                    # CLI: python main.py --input documents/ --output output/
├── output/records/ + output/exceptions_report.md
└── tests/                     # validadores, classifier rules, repository — SEM chamadas de LLM
```

## Ordem de implementação (respeitar — evita gastar token cedo)

1. Schemas Pydantic + `GoldenRecordsRepository` + validadores determinísticos **com testes** (roda sem API key)
2. Ingestão + detecção nativo/escaneado
3. Extração nativa (structured output) → rodar docs 01–06, 08
4. Classificador → conferir doc 03
5. Cadeia de validação + scorer + roteamento → conferir doc 08
6. Rota multimodal → doc 07
7. Output builder + relatório de exceções
8. README + ADRs finais

## Convenções de código

- Type hints em tudo; Pydantic v2 (`model_validate`, `field_validator`)
- Funções pequenas e nomeadas pelo que fazem; sem classes onde função basta
- Valores monetários: `Decimal`, nunca float
- Datas: `datetime.date`, parse explícito do formato brasileiro (dd/mm/yyyy e datas por extenso)
- Sem dependência nova sem justificar em ADR
- Todo comportamento não-óbvio referencia o ADR correspondente em comentário


## Modelos LLM (decisão travada)
- Modelo é SEMPRE configuração via settings/.env, nunca hardcoded.
- Três knobs independentes: EXTRACTION_MODEL, CLASSIFICATION_MODEL, VISION_MODEL.
- Default dos três: gpt-5.4-mini (tier mini; sobe de tier apenas se o lote provar erro — ADR).
- Structured outputs via client.beta.chat.completions.parse() com o modelo Pydantic direto (strict).

## O que NUNCA fazer

- Não adicionar LangGraph/LangChain "para organizar"
- Não validar com LLM o que código valida
- Não usar float para dinheiro
- Não fazer retry silencioso em baixa confiança
- Não inventar valores para campos ausentes — `null` + justificativa
- Não passar PDFs nativos pela rota multimodal
