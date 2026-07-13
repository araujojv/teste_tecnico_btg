# ADR-001 - Pipeline sem framework de agentes

## Status

Accepted

## Contexto

O fluxo é um DAG linear com dois ramos (PDF nativo vs escaneado). Frameworks
como LangGraph/LangChain adicionam abstração, dependência e superfície de
debug para um `if` sobre `pdf_kind`.

Há sessão técnica ao vivo (45 min) para estender e depurar o código: legibilidade
e previsibilidade importam mais que orquestração genérica.

## Decisão

- Python 3.11+, Pydantic v2, SDK OpenAI direto.
- Cada etapa é uma função pura `(DocumentState) -> DocumentState`.
- Orquestrador simples em `src/pipeline/orchestrator.py` encadeia ingest ->
  extract -> classify -> validate -> score -> route.
- Sem LangGraph, LangChain ou frameworks de agente.

## Consequências

- Troca de provider fica atrás de `LLMProvider` (ADR relacionado ao adapter).
- Extensões na sessão ao vivo são locais (um step, um validador), sem grafo.
- Custo cognitivo menor; trade-off: não há runtime de agente out-of-the-box
  (checkpoints, retries de grafo) - é intencional.
