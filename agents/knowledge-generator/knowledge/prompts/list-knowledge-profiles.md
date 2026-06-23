# Prompt: List Knowledge Profiles

## Objetivo
Ajudar o usuario/host a escolher o profile certo antes de gerar knowledge.

## Entradas
Nenhuma. A capability retorna o catalogo de profiles (id, name, description,
source_kinds, required_artifacts).

## Passos de raciocinio
1. Apresente os 9 profiles agrupados por natureza: codigo
   (`code-project`, `frontend-app`), documentacao (`documentation-set`),
   dominio/negocio (`business-domain`, `integration-docs`, `support-operations`),
   dados (`data-domain`) e fallback (`mixed-knowledge`, `freeform`).
2. Para cada profile relevante ao caso do usuario, explique QUANDO usa-lo e quais
   `required_artifacts` ele exige.
3. Se o usuario descreveu a fonte, recomende 1 profile primario e 1 alternativo.

## Regras de decisao
- So existem os 9 profiles do catalogo; nunca invente um novo.
- Em duvida entre codigo e dominio, recomende inspecionar a fonte primeiro
  (`inspect-source`).

## Saida
Lista enxuta: por profile -> quando usar + artefatos. Encerrar com a recomendacao.

## NAO fazer
Nao gere knowledge nem acesse filesystem externo aqui.
