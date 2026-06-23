# Prompt: explore-database-domain

## OBJETIVO
Agrupar tabelas em domínios de negócio (customer, sales, finance, audit,
security, other) por heurística de nome para dar uma visão geral do modelo.

## ENTRADAS
- `schema` (opcional): restringir ao schema.
- `limit` (opcional, default 200).

## RACIOCÍNIO (passos)
1. Execute a capability `explore-database-domain`.
2. Leia `domains[]` (campos: `domain`, `table_count`) e `tables[]`.
3. Identifique o domínio com mais tabelas — tende a ser o núcleo do sistema.
4. Destaque tabelas sem domínio claro (`other`) — podem ser auxiliares ou
   legado.

## RUBRICA / REGRAS DE DECISÃO
- O agrupamento é **inferência heurística por nome** (não metadado oficial).
  Sempre deixe isso explícito.
- `other` grande → banco com nomenclatura pouco padronizada; sugira inspecionar
  manualmente com `describe-table`.

## SAÍDA
Tabela de `domain` × `table_count` + nota de inferência.
Lista de tabelas por domínio (colapsada se > 10 por domínio).

## NÃO FAÇA
- Não apresente os domínios como agrupamento oficial do banco.
- Não omita o aviso de que é inferência por padrão de nome.
