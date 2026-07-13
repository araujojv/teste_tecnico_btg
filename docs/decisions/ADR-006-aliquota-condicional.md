# ADR-006 - Alíquota de IR não é atributo genérico do evento

## Status

Accepted

## Contexto

Avisos de dividendo (ex. doc 01) citam IRRF em regras gerais, limiares ou
isenções condicionais (ex. retenção acima de R$ 50 mil) que **não** são a
alíquota do provento por ação. Preencher `aliquota_ir` nesses casos quebra
`gross_net_consistency` e distorce o registro fiscal.

## Decisão

No prompt de extração: `aliquota_ir` só quando a taxa se aplica **explicitamente
a este evento** (ex. JCP com IRRF 17,5% na fonte sobre o valor bruto).
Menção genérica/condicional/limiar -> `null`.

`aliquota_ir` é fração (`0.175`), nunca percentual textual.

## Consequências

- Doc 01: alíquota null; gross_net pode warning por campos ausentes (ok).
- Doc 03/JCP: alíquota 0.175; check bruto*(1-aliquota)~=liquido.
- Evita inventar tributação a partir de notas de rodapé legislativas.
