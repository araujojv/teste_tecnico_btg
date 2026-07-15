# Guia de defesa — sessão técnica 45 min (Tech Lead)

Objetivo: defender o projeto com clareza, mostrar domínio do código e das
decisões, e estar pronto para estender/depurar ao vivo.

Fonte canônica: `README.md` + `docs/decisions/` + `output/`. Este guia é o
roteiro de estudo e argumentação.

---

## 1. Pitch de abertura (60–90 segundos)

Memorize e diga com calma:

> “O problema é transformar avisos B3/CVM em registros auditáveis. Erro de
> classificação aqui é erro tributário — JCP tem IRRF na fonte; dividendo comum,
> não. A tese da arquitetura é: **a LLM extrai e classifica; código
> determinístico valida; baixa confiança vai para humano com justificativa —
> nunca retry silencioso**. O pipeline é um DAG linear com um `if` (nativo vs
> escaneado): ingest → extract → classify → validate → score → route. No lote
> de 8 docs, as armadilhas foram detectadas cada uma por um motivo distinto.”

Se pedirem o resultado em uma frase:

| Docs | Rota | Motivo |
|------|------|--------|
| 01, 02, 04, 06 | auto_approve | limpos (warnings não bloqueiam) |
| 03 | human_review | título “Dividendos”, conteúdo JCP |
| 05 | human_review | datas incoerentes no PDF |
| 07 | human_review | OCR, overall &lt; 0.85 |
| 08 | human_review | emissor fora do golden_records |

---

## 2. A tese — o que você está defendendo

Três frases que sustentam tudo:

1. **Separação de responsabilidades.** LLM é boa em linguagem (extrair,
   classificar). Código é bom em regras (datas, bruto/líquido, ISIN, cadastro).
   Misturar os dois mascara falha e dificulta teste.
2. **Incerteza explícita.** Em Asset Servicing, “retry até passar” esconde
   risco. Preferimos `human_review` com motivo auditável.
3. **Simplicidade para a sessão ao vivo.** Sem LangGraph: funções puras
   `(DocumentState) → DocumentState`. Extender = um step ou um validador novo.

Quando o TL perguntar “por que não um agent framework?”, responda com ADR-001:
o fluxo é um DAG com 2 branches; framework adiciona dependência e opacidade
sem resolver problema existente. Se amanhã precisar de grafo, a migração é
natural porque o estado já é Pydantic append-only.

---

## 3. Fluxo mental (desenhe no quadro se pedirem)

```
PDF
 └─ ingest (pdfplumber + densidade)
      ├─ native  → extract (EXTRACTION_MODEL, structured output strict)
      └─ scanned → extract OCR (VISION_MODEL, mesmas imagens)
           └─ classify (raciocínio ANTES do tipo — schema ordered)
                └─ validate (5 regras em código)
                     └─ score (heurística + justificativa)
                          └─ route (precedência fixa)
                               └─ JSON + exceptions_report.md
```

Arquivos-âncora para abrir ao vivo:

| Tema | Arquivo |
|------|---------|
| Orquestração | `src/pipeline/orchestrator.py` |
| Roteamento | `src/pipeline/steps/route.py` |
| Schema classificação | `src/classification/schemas.py` |
| Prompt sinais JCP | `src/classification/prompts.py` |
| Datas | `src/validation/rules/date_coherence.py` |
| Golden | `src/validation/rules/golden_records.py` |
| Adapter LLM | `src/llm/provider.py` + `openai_provider.py` |
| Estado | `src/pipeline/state.py` |
| Saída | `src/output/record_builder.py` |

---

## 4. Cartões de decisão (decorar o “por quê”)

Para cada decisão: **o que** → **por quê** → **trade-off** → **como atacariam**.

### D1 — Sem LangGraph / LangChain (ADR-001)

- **O que:** Python + Pydantic + SDK OpenAI; orquestrador encadeia steps.
- **Por quê:** DAG linear + 1 branch; sessão de 45 min exige legibilidade.
- **Trade-off:** sem checkpoints/retries de framework — intencional.
- **Ataque:** “E se o fluxo crescer?” → steps já são puros; plugar grafo depois
  sem reescrever domínio. Interface `LLMProvider` / `EventClassifier` isolam troca.

### D2 — Structured outputs strict (ADR-003)

- **O que:** `chat.completions.parse()` com schema Pydantic strict.
- **Por quê:** contrato garantido pela API, não só “JSON válido”; falha cedo.
- **Trade-off:** schema da LLM é intermediário (strings); mapper vira
  `Decimal`/`date`/`EventType` no código.
- **Ataque:** “Por que não tool calling para validar?” → validação é código
  testável (pytest, 0 token). Tool calling seria custo e não-determinismo.

### D3 — Classificação autoregressiva (ordem dos campos)

- **O que:** `evidencias → raciocinio → tipo_declarado_no_titulo → tipo_evento → divergencia`.
- **Por quê:** LLM gera token a token; forçar raciocínio **antes** condiciona
  a escolha do tipo. Doc 03: título engana; conteúdo tem TJLP + IRRF 17,5% +
  imputação art. 9º Lei 9.249/95 → `jcp`.
- **Sanidade matemática (decore):** `0,09215 × (1 − 0,175) = 0,07602375`.
- **Ataque:** “E se a LLM mentir no raciocínio?” → validação + confiança +
  rota humana na divergência; não confiamos só no texto.

### D4 — Multimodal só quando necessário (ADR-007)

- **O que:** densidade de texto &lt; limiar → scanned → imagens + visão.
- **Por quê:** nativos têm ~1k–1.5k chars/página; doc 07 tem 0. Imagem custa.
- **Trade-off:** docs mistos (página nativa + escaneada) exigiriam detecção
  por página — limitação conhecida.
- **Ataque:** “Por que não Tesseract?” → layout tabular de aviso; um motor
  (visão + mesmo schema) evita segunda pipeline de texto.

### D5 — Validação determinística em cadeia

Cinco validadores, cada um `pass|fail|warning|not_applicable`:

1. **golden_records** — ISIN/ticker/CNPJ/nome fuzzy (Repository CSV)
2. **date_coherence** — `aprovação ≤ com < ex ≤ pagamento` (ADR-002)
3. **gross_net** — `bruto × (1 − alíquota) ≈ líquido`
4. **isin_checksum** — ISO 6166; golden confirma → warning (ADR-004)
5. **type_consistency** — só consome `divergencia_titulo_conteudo` (ADR-005)

- **Por quê em código:** testável, barato, auditável. Doc 05 foi pego por
  regra, não por prompt.
- **Ataque:** “Por que Chain of Responsibility?” → cada regra isolada,
  adicionar validador = uma classe + registrar na cadeia, sem misturar.

### D6 — Ausência declarada ≠ falha (doc 04)

- Pagamento “será oportunamente definida” → `null` +
  `data_pagamento_ausente_declarada=true` → **warning**, não fail.
- **Por quê:** o documento admite a ausência; inventar data seria pior.

### D7 — Alíquota condicional não entra (ADR-006 / doc 01)

- Menção a IRRF 10% acima de R$ 50 mil/mês **não** é alíquota do evento.
- Capturar como flat quebraria gross/net e inventaria tributação.
- JCP com 17,5% na fonte **sim** preenche `aliquota_ir` (fração `0.175`).

### D8 — golden_records > checksum (ADR-004)

- ISINs do lote são fictícios; checksum puro derrubaria docs válidos.
- Confirmado no golden → warning; ausente (doc 08) → fail.

### D9 — Confiança heurística com justificativa

- Base nativo 0.90 / OCR 0.70; ajustes por validator e divergência.
- **Não** é probabilidade calibrada — diga isso proativamente.
- Campo crítico `low` (tipo_evento, valor_bruto, data_com) → human_review.

### D10 — Política de roteamento (ordem de precedência)

1. fail golden_records  
2. fail datas ou bruto/líquido  
3. campo crítico low  
4. OCR overall &lt; 0.85  
5. senão auto_approve (warnings no relatório)

**Nunca** retry silencioso.

### D11 — Modelo como config (ADR-008)

- `EXTRACTION_MODEL` / `CLASSIFICATION_MODEL` / `VISION_MODEL`
- Default mini; subir tier só com evidência de erro sistemático.

### D12 — O que você NÃO fez (defesa forte)

| Não fiz | Por quê |
|---------|---------|
| RAG / vector store | 8 docs curtos cabem no contexto |
| Retry em baixa confiança | mascara incerteza regulatória |
| OCR local (Tesseract) | visão + mesmo schema; custo documentado |
| Classificador treinado | sem dataset; interface `EventClassifier` pronta para trocar |
| Fila real de revisão | relatório é o contrato; rota isolada para plugar depois |
| Framework de agentes | ver D1 |

---

## 5. Gabarito do lote — estudar documento a documento

### 01 — Energética Vale do Tietê (dividendo) → auto_approve

- Extração limpa; golden pass.
- `aliquota_ir=null` (IRRF condicional 2026) → warning gross_net por campos
  ausentes — **esperado**, não bug.
- isin_checksum warning (ISIN fictício confirmado no golden).

**Frase pronta:** “Aprovei com warning porque a alíquota mencionada no aviso
não é atributo flat do evento; inventá-la distorceria o líquido.”

### 02 — Banco Meridional (JCP) → auto_approve

- JCP claro; IRRF na fonte; overall alto (~0.93).
- Só warning de checksum fictício.

### 03 — Siderúrgica Paranaense → human_review (**estrela da apresentação**)

- Título: Dividendos. Conteúdo: JCP (TJLP, IRRF 17,5%, imputação ao
  obrigatório).
- `tipo_evento=jcp`, `divergencia_titulo_conteudo=true`.
- Confiança de `tipo_evento` cai (type_consistency warning + divergência)
  → regra 3 do roteamento.
- Check: `0,09215 × 0,825 = 0,07602375`.

**Frase pronta:** “Se eu tivesse classificado pelo título, erraria o
tratamento tributário. O schema força evidência e raciocínio antes do enum;
o validador não refaz string matching — consome a flag do classificador
(ADR-005), porque matching de título gerava falso positivo por acento.”

### 04 — Rede Varejo (JCP sem data) → auto_approve

- Pagamento ausente **declarado** → warning date_coherence, não fail.
- Demonstra ADR-002: ausência consciente ≠ incoerência.

### 05 — Aurora Saneamento → human_review (**vitória da validação**)

- PDF: pagamento 10/07 **antes** de data-com 15/07 e ex 16/07.
- `date_coherence=fail` → human_review.
- Narrativa forte: armadilha detectada pela regra; o PDF é inconsistente;
  não “corrigimos” datas — evidência literal fica, operador revisa.

**Frase pronta:** “Validação em código pegou um caso que um prompt otimista
passaria. Não inventamos data coerente.”

### 06 — Petroquímica Litoral (grupamento) → auto_approve

- Proporção, não dinheiro; gross_net `not_applicable`.
- Limpo operacionalmente.

### 07 — Telecom Norte SCAN → human_review

- Densidade 0 → rota multimodal; `method=ocr`; teto de confiança menor.
- overall ~0.74 &lt; 0.85 → human_review mesmo com validadores ok.
- Cross-checks: bruto×(1−0,175)=líquido; ISIN/ticker no golden.

**Frase pronta:** “Li o escaneado, mas admito incerteza do método. Em
produção eu preferiria humano a auto-aprovar OCR no limite.”

### 08 — Construtora Horizonte → human_review

- Emissor/ISIN/ticker **não existem** no golden_records.
- fail golden (precedência 1) + fail checksum.
- Bonificação correta; o bloqueio é cadastro, não classificação.

**Frase pronta:** “Emissor não cadastrado é risco regulatório — precedência
máxima no roteamento, independente da qualidade da extração.”

---

## 6. Perguntas prováveis do Tech Lead (Q&A)

### Arquitetura

**Q: Por que não LangGraph?**  
A: DAG com um `if`. Framework = custo cognitivo na sessão ao vivo. Estado
já é função pura; migração futura é possível.

**Q: Onde está o acoplamento com OpenAI?**  
A: Só atrás de `LLMProvider`. Pipeline recebe o adapter; troca de provider
não toca steps.

**Q: Por que três modelos?**  
A: Tarefas diferentes (texto / classificação / visão). Knobs no `.env`;
default mini; sobe tier com evidência (ADR-008).

### Domínio / tributário

**Q: Diferença dividendo vs JCP?**  
A: JCP: limitado à TJLP, IRRF 15/17,5% na fonte, imputável ao dividendo
obrigatório (Lei 9.249/95 art. 9º). Dividendo: distribuição de lucro; sem
alíquota flat do evento no aviso típico.

**Q: Por que doc 03 é human_review se a classificação está certa?**  
A: Divergência título/conteúdo rebaixa confiança de `tipo_evento` (campo
crítico). Prefiro humano confirmar o tratamento tributário quando o título
contradiz o corpo.

### Validação / confiança

**Q: Confiança é probabilidade?**  
A: Não. Score heurístico com sinais verificáveis e justificativa. Calibrar
exigiria conjunto rotulado.

**Q: Por que warnings não bloqueiam?**  
A: Precedência explícita: só fail (e low em crítico / OCR baixo) bloqueiam.
Warnings vão ao relatório para o operador ver sem parar o fluxo.

**Q: ISINs inválidos e mesmo assim auto_approve?**  
A: Lote sintético. Hierarquia: golden confirma → warning. Em produção com
ISIN real o warning some; a regra continua segura (ADR-004).

### Extensão ao vivo (ensaiar)

Peça mental: “adicione um validador X” / “force human_review se Y” /
“troque o limiar OCR”.

Checklist de extensão segura:

1. Novo validador em `src/validation/rules/` implementando `Validator`
2. Registrar na cadeia em `validate.py`
3. Teste em `tests/` sem LLM
4. Se afetar rota: regra em `route.py` com precedência documentada
5. Se afetar score: mapear campo em `_FIELD_VALIDATORS` no scorer

Debug ao vivo:

- Relatório: `output/exceptions_report.md`
- JSON: `output/records/<doc>.json` → `validation`, `route`, `audit_trail`
- Reprocessar um PDF: `python main.py --input documents/03_....pdf --output output/`
- Suite rápida: `pytest` (sem API key)

---

## 7. Roteiro sugerido da call (45 min)

| Min | O quê |
|-----|--------|
| 0–3 | Pitch + tese (seção 1–2) |
| 3–12 | Fluxo + decisões D1–D5 (quadro/código) |
| 12–22 | Walkthrough do lote: 03, 05, 07, 08 (as 4 human_review) |
| 22–28 | O que NÃO fiz + limitações honestas |
| 28–45 | Hands-on: estender/depurar o que pedirem |

Priorize **03 e 05** se o tempo apertar: mostram classificação + validação
determinística — o coração do case.

---

## 8. Checklist de estudo (até sexta)

Dia a dia sugerido (ajuste ao seu tempo):

**Passagem 1 — mapa**  
- [ ] Ler README inteiro  
- [ ] Ler os 8 ADRs em `docs/decisions/`  
- [ ] Abrir `exceptions_report.md` e cruzar com a tabela do gabarito  

**Passagem 2 — código**  
- [ ] `orchestrator.py` → seguir cada step  
- [ ] `classification/schemas.py` + `prompts.py` (ordem + sinais JCP)  
- [ ] `route.py` (decorar as 5 regras)  
- [ ] Um validador por vez: golden, date, gross_net, isin, type  
- [ ] `scorer.py` (bases 0.90 / 0.70)  
- [ ] Abrir 1 JSON de auto_approve e 1 de human_review  

**Passagem 3 — oral**  
- [ ] Gravar o pitch de 90s  
- [ ] Explicar doc 03 em 2 minutos sem olhar nota  
- [ ] Explicar doc 05 + por que validação ≠ LLM  
- [ ] Listar de cabeça o que NÃO fez e por quê  
- [ ] Simular: “adicione validador de CNPJ checksum” (onde mexeria?)  

**Passagem 4 — ambiente**  
- [ ] `pytest` verde local  
- [ ] Saber onde está `.env.example` e os 3 knobs de modelo  
- [ ] Ter o repo aberto no editor com favoritos nos arquivos-âncora  

---

## 9. Frases de ouro (use com parcimônia)

1. “LLM extrai e classifica; código valida; incerteza vai para humano.”
2. “Retry silencioso em contexto regulatório mascara risco.”
3. “Classifico pelo conteúdo, nunca pelo título — doc 03 prova o porquê.”
4. “Não invento campo ausente: null + justificativa.”
5. “Confiança sem justificativa não é auditável.”
6. “O operador audita o JSON sem reabrir o PDF — cada campo tem snippet,
   página e método.”

---

## 10. Limitações — diga antes de perguntarem

- Densidade **média** por documento (mistos exigiriam por página).
- Confiança não calibrada.
- Golden records em CSV (Repository permite trocar por API).
- Sem fila de workflow humano — só o relatório.
- Classificador LLM: em volume, supervisionado seria mais barato
  (`EventClassifier` isola a troca).

Honestidade aqui aumenta credibilidade com o TL.
