# Prompt: list-databases

> Operação read-only. Aplique limite. Separe dados coletados de inferências.

## Objetivo
Listar todos os databases acessíveis no servidor PostgreSQL para orientar a
seleção do banco alvo. Não lê linhas de dados.

## Entradas esperadas
- `database` (opcional): nome do banco de conexão inicial (usa padrão se omitido).
- `limit` (opcional, default 200): máximo de databases a retornar.

## Passos de raciocínio
1. Execute `list-databases` com o limit informado.
2. Leia `count` e a lista `databases`.
3. Apresente os resultados em tabela com `database_name` e `owner_name`.
4. Destaque se o banco solicitado pelo usuário está na lista.

## Regras de decisão
- Se 0 resultados, informe que não foram encontrados databases acessíveis ao usuário atual.
- Não sugira banco "certo" sem evidência — apenas liste o que foi retornado.

## Saída
Tabela markdown: `database_name`, `owner_name` + contagem total.

## NÃO faça
- Não exiba dados de tabelas ou schemas aqui.
- Não afirme que um database existe sem que apareça no resultado.
