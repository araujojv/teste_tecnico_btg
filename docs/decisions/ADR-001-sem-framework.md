# ADR-001 - Pipeline sem framework de agentes

## Status

Accepted

## Contexto

O fluxo e um DAG linear com dois ramos (PDF nativo vs escaneado). Frameworks
como LangGraph/LangChain adicionam abstracao, dependencia e superficie de
debug para um `if` sobre `pdf_kind`.

Ha sessao tecnica ao vivo (45 min) para estender e depurar o codigo: legibilidade
e previsibilidade importam mais que orquestracao generica.

## Decisao

- Python 3.11+, Pydantic v2, SDK OpenAI direto.
- Cada etapa e uma funcao pura `(DocumentState) -> DocumentState`.
- Orquestrador simples em `src/pipeline/orchestrator.py` encadeia ingest ->
  extract -> classify -> validate -> score -> route.
- Sem LangGraph, LangChain ou frameworks de agente.

## Consequencias

- Troca de provider fica atras de `LLMProvider` (ADR relacionado ao adapter).
- Extensoes na sessao ao vivo sao locais (um step, um validador), sem grafo.
- Custo cognitivo menor; trade-off: nao ha runtime de agente out-of-the-box
  (checkpoints, retries de grafo) — e intencional.
