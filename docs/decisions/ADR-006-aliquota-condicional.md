# ADR-006 - Aliquota de IR nao e atributo generico do evento

## Status

Accepted

## Contexto

Avisos de dividendo (ex. doc 01) citam IRRF em regras gerais, limiares ou
isencoes condicionais (ex. retencao acima de R$ 50 mil) que **nao** sao a
aliquota do provento por acao. Preencher `aliquota_ir` nesses casos quebra
`gross_net_consistency` e distorce o registro fiscal.

## Decisao

No prompt de extracao: `aliquota_ir` so quando a taxa se aplica **explicitamente
a este evento** (ex. JCP com IRRF 17,5% na fonte sobre o valor bruto).
Mencao generica/condicional/limiar -> `null`.

`aliquota_ir` e fracao (`0.175`), nunca percentual textual.

## Consequencias

- Doc 01: aliquota null; gross_net pode warning por campos ausentes (ok).
- Doc 03/JCP: aliquota 0.175; check bruto*(1-aliquota)~=liquido.
- Evita inventar tributacao a partir de notas de rodape legislativas.
