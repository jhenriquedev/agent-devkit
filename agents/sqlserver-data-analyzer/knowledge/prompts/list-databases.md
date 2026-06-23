# Prompt: list-databases

## OBJETIVO
Descobrir os bancos ONLINE disponíveis na instância SQL Server.

## ENTRADAS
- `limit` (opcional, default 200): número máximo de bancos a retornar.

## RACIOCÍNIO (passos)
1. Execute a capability `list-databases`.
2. Leia `count` e a lista `databases[]` (campos: `database_name`, `state_desc`,
   `compatibility_level`).
3. Destaque contagem total; aponte bancos relevantes ao objetivo do usuário.

## RUBRICA / REGRAS DE DECISÃO
- Se o usuário tem um objetivo específico (ex.: "quero analisar clientes"),
  sugira usar `--database <nome>` e depois `list-schemas`/`list-tables`.
- Não liste mais de `limit` bancos; avise se `count == limit` (pode haver mais).

## SAÍDA
Tabela enxuta com `database_name`, `state_desc`, `compatibility_level` +
contagem total.

## NÃO FAÇA
- Não retorne o catálogo inteiro sem limite.
- Não exponha detalhes de configuração interna (collation, versão de loopback).
