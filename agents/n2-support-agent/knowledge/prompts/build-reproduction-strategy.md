# Build Reproduction Strategy

## Objetivo

Definir a estrategia TDD de reproducao antes do patch.

## Entradas

- Contexto N2.
- Achados de codigo ranqueados.
- Sintoma e evidencias.

## Raciocinio

1. Escolha o arquivo de codigo primario.
2. Infira arquivo de teste correspondente.
3. Descreva o estado inicial em `given`.
4. Descreva o fluxo afetado em `when`.
5. Descreva o comportamento esperado em `then`.
6. Liste etapas red, green e refactor.

## Rubrica/Regras

- Teste deve reproduzir sintoma, nao apenas cobrir linha.
- O alvo deve preferir arquivo source.
- Sem arquivo candidato, deixar alvo placeholder e readiness bloqueia.

## Saida

JSON com `testPlan.testFile`, `targetFile`, `given`, `when`, `then` e
`redGreenRefactor`.

## Nao faca

- Nao implementar o teste.
- Nao propor refactor amplo.
