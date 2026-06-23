# Prompt: generate-erd-report

## OBJETIVO
Gerar um diagrama ERD em Mermaid a partir das FKs declaradas no banco.

## ENTRADAS
- `schema` (opcional): filtrar por schema.
- `limit` (opcional, default 500).

## RACIOCÍNIO (passos)
1. Execute a capability `generate-erd-report`.
2. O runner renderiza automaticamente o bloco `erDiagram` mermaid.
3. Se `count == 0`, declare "nenhum relacionamento declarado" e não gere
   diagrama vazio.

## RUBRICA / REGRAS DE DECISÃO
- O ERD reflete apenas **FKs declaradas** (constraint real), não heurísticas.
- Cardinalidade exibida (`}o--||`) é genérica FK; não representa multiplicidade
  real verificada por dados.
- Se banco não usa FKs, sugira `suggest-joins` e avise que o ERD estará vazio.

## SAÍDA
Bloco mermaid `erDiagram` + nota de que reflete FKs declaradas.
Se vazio: mensagem explicativa com sugestão de próximo passo.

## NÃO FAÇA
- Não invente relacionamentos que não existem como FK.
- Não confunda heurística de join com FK real no diagrama.
