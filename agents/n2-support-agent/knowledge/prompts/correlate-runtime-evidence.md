# Correlate Runtime Evidence

## Objetivo

Cruzar evidencia runtime, card/N1 e achados de codigo.

## Entradas

- Contexto N2.
- Evidencias do N1.
- Resultado de analise de codigo.

## Raciocinio

1. Liste evidencias que confirmam a hipotese.
2. Liste contradicoes entre checks e estado esperado.
3. Liste lacunas que impedem conclusao segura.
4. Inclua gaps N1 abertos como lacunas.
5. Preserve rastreabilidade para arquivos candidatos.

## Rubrica/Regras

- Evidencia confirmada deve citar fonte.
- Contradicao deve explicar os dois lados.
- Lacuna nao vira conclusao negativa.

## Saida

JSON com `confirmedEvidence`, `contradictions` e `missingEvidence`.

## Nao faca

- Nao classifique causa raiz.
- Nao omita lacunas abertas.
- Nao invente resultado de log ou banco.
