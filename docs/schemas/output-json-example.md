# Contrato do JSON de saida (exemplo: doc 01)

Arquivo gerado por `record_builder` em `output/records/<doc_id>.json`.
Serializacao UTF-8; `Decimal` como string; datas ISO (`YYYY-MM-DD`).

Exemplo real (recorte comentado) de
`01_energetica_vale_tiete_dividendo`:

```json
{
  "doc_id": "01_energetica_vale_tiete_dividendo",

  "processing": {
    "timestamp": "2026-07-11T16:55:02.822079+00:00",
    "pipeline_version": "0.1.0",
    "source_path": ".../documents/01_energetica_vale_tiete_dividendo.pdf",
    "pdf_kind": "native",
    "extraction_method": "native",
    "models": {
      "extraction": "gpt-5.4-mini",
      "classification": "gpt-5.4-mini",
      "vision": "gpt-5.4-mini"
    },
    "overall_confidence": 0.8464285714285714
  },

  "record": {
    "emissor": {
      "value": "ENERGETICA VALE DO TIETE S.A.",
      "confidence": {
        "level": "high",
        "score": 0.95,
        "justification": "...",
        "signals": ["extraction_method=native (+0.90 base)", "validator:golden_records=pass (+0.05)"]
      },
      "evidence": {
        "snippet": "ENERGETICA VALE DO TIETE S.A.",
        "page": 1,
        "method": "native"
      }
    },
    "isin": {
      "value": "BRTIETACNOR3",
      "confidence": { "level": "high", "score": 0.95 },
      "evidence": { "snippet": "(ISIN BRTIETACNOR3)", "page": 1, "method": "native" }
    },
    "tipo_evento": {
      "value": "dividendo",
      "confidence": { "level": "high", "score": 0.95 },
      "evidence": { "snippet": "...", "page": 1, "method": "native" }
    },
    "tipo_declarado_no_titulo": {
      "value": "Pagamento de Dividendos",
      "confidence": null,
      "evidence": { "snippet": "AVISO AOS ACIONISTAS ...", "page": 1, "method": "native" }
    },
    "divergencia_titulo_conteudo": { "value": false, "confidence": null, "evidence": null },
    "data_com": {
      "value": "2026-06-12",
      "confidence": { "level": "high", "score": 0.95 },
      "evidence": { "snippet": "Data-base (\"data com\") 12/06/2026", "page": 1, "method": "native" }
    },
    "valor_bruto": {
      "value": "0.4275000000",
      "confidence": { "level": "medium", "score": 0.7 },
      "evidence": { "snippet": "Valor bruto por acao ordinaria R$ 0,4275000000", "page": 1, "method": "native" }
    },
    "aliquota_ir": {
      "value": null,
      "confidence": { "level": "low", "score": 0.5 },
      "evidence": null
    }
  },

  "validation": [
    {
      "rule": "golden_records",
      "status": "pass",
      "message": "Match by isin: ...",
      "details": { "method": "isin", "score": 1.0 }
    },
    {
      "rule": "isin_checksum",
      "status": "warning",
      "message": "ISIN checksum invalid (...), but ISIN confirmed in golden_records...",
      "details": { "confirmed_in_golden_records": true }
    }
  ],

  "routing": {
    "decision": "auto_approve",
    "reasons": [
      "auto_approve with warnings: gross_net_consistency, isin_checksum"
    ]
  },

  "audit_trail": [
    "ingest: kind=native, ...",
    "extract_native: ...",
    "classify: mode=text, tipo_evento=dividendo, ...",
    "validate: ...",
    "score: overall=0.846, ...",
    "route: decision=auto_approve; ..."
  ]
}
```

## Campos de topo

| Campo | Significado |
|-------|-------------|
| `doc_id` | stem do PDF |
| `processing` | metadados de execucao, modelos, metodo, overall |
| `record.<campo>` | `value` + `confidence` + `evidence` (snippet/pagina/metodo) |
| `validation` | lista de `ValidationResult` |
| `routing` | `auto_approve` ou `human_review` + reasons |
| `audit_trail` | log append-only das etapas |

JSON completo do lote: `output/records/` (apos `python main.py`).
