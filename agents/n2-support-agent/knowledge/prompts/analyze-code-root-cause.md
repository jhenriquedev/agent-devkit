# Analyze Code Root Cause

## Objetivo

Localizar arquivos, metodos e regras candidatos a causa raiz.

## Entradas

- `--codebase-path`.
- Sintoma, evidencias e entidades do contexto N2.
- Contrato N1 quando existir.

## Raciocinio

1. Derive tokens do sintoma e das evidencias.
2. Varra arquivos de codigo suportados.
3. Ignore diretorios de build, vendor, venv e cache.
4. Pontue ocorrencias no caminho e no conteudo.
5. Classifique o achado como source, migration, test ou support.
6. Liste metodos assinaturas relevantes.

## Rubrica/Regras

- Priorize source sobre migration, test e support.
- Arquivo de teste e pista, nao alvo primario.
- Sem `codebase_path`, retorne `skipped`.
- Caminho inexistente vira `unavailable`.

## Saida

JSON com `filesInspected`, `relevantMethods`, `businessRulesFound`,
`technicalFindings`, `status` e `reason`.

## Nao faca

- Nao proponha patch.
- Nao rode comandos no projeto analisado.
- Nao leia arquivos gigantes sem limite.
