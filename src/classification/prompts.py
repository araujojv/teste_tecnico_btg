"""Prompts for corporate-event type classification."""

from __future__ import annotations


CLASSIFICATION_SYSTEM = """\
You classify Brazilian corporate-event notices (B3/CVM) by DOCUMENT CONTENT.

Critical rules:
- Classify by the CONTENT of the notice, NEVER by the title alone.
- First quote literal evidence snippets, THEN reason, THEN choose the type \
(schema field order enforces this).
- tipo_declarado_no_titulo: the event type as it appears LITERALLY in the \
title/header (e.g. "Distribuicao de Dividendos", "Pagamento de Dividendos"). \
null ONLY if the title/header does not indicate a type.
- tipo_evento: one of dividendo | jcp | bonificacao | grupamento, based on content.
- divergencia_titulo_conteudo=true when title and content point to different types.

Deterministic signals by type:

JCP (juros sobre capital proprio):
- Remuneration limited to TJLP (Taxa de Juros de Longo Prazo) / pro rata die TJLP.
- IRRF withheld at source at 15% or 17.5%.
- Amount imputed to the mandatory minimum dividend (art. 9 Lei 9.249/95).
- Often labeled "remuneracao do capital proprio" in the body even if the title \
says "Dividendos".

Dividendo:
- Distribution of profits/earnings to shareholders.
- No flat IRRF withholding on the event itself (general/conditional tax mentions \
do not turn a dividend into JCP).

Bonificacao:
- Capitalization of reserves with issuance of new shares in a stated proportion.
- No cash distribution of the event itself.

Grupamento:
- Reduction of the number of shares in a stated proportion.
- No distribution of cash/provento.
"""


def build_classification_user_prompt(page_texts: list[str]) -> str:
    """Build user message with numbered pages for evidence grounding."""
    parts: list[str] = [
        "Classify the corporate-event type from the following document pages.",
        "Follow the schema field order: evidence -> reasoning -> title type -> "
        "content type -> divergence flag.",
        "",
    ]
    for index, text in enumerate(page_texts, start=1):
        parts.append(f"--- PAGE {index} ---")
        parts.append(text if text.strip() else "(no extractable text)")
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def build_classification_vision_user_content(
    page_images_base64: list[str],
) -> list[dict]:
    """Multimodal classification content from scanned page images."""
    content: list[dict] = [
        {
            "type": "text",
            "text": (
                "Classify the corporate-event type from the following scanned "
                "document page images. Each image is labeled PAGE N (1-based). "
                "Follow the schema field order: evidence -> reasoning -> title "
                "type -> content type -> divergence flag. "
                "Quote evidence as literal transcriptions from the images."
            ),
        }
    ]
    for index, image_b64 in enumerate(page_images_base64, start=1):
        content.append({"type": "text", "text": f"--- PAGE {index} ---"})
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_b64}",
                },
            }
        )
    return content
