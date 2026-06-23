# Prompt: compare-tables

> Operação read-only. Não leia dados de linha. Separe dados coletados de inferências.

## Objetivo
Comparar a estrutura de duas tabelas (colunas em comum, exclusivas de cada lado) para
identificar divergências de schema, por exemplo em ambientes diferentes ou tabelas
relacionadas.

## Entradas esperadas
- `left-schema` e `left-table` (obrigatórios).
- `right-schema` e `right-table` (obrigatórios).
- `database` (opcional).

## Passos de raciocínio
1. Confirme que todos os 4 parâmetros foram fornecidos.
2. Execute `compare-tables`.
3. Classifique colunas em:
   - **common**: presentes em ambas (mesmo nome e tipo ou só nome?).
   - **left_only**: só na tabela esquerda.
   - **right_only**: só na tabela direita.
4. Destaque divergências de tipo para colunas comuns (se disponível).

## Regras de decisão
- Se uma tabela não existir, o runner retorna erro — informe ao usuário.
- Colunas com mesmo nome mas tipos diferentes → sinalizar como divergência.
- Foco em estrutura, não em conteúdo.

## Saída
3 seções:
### Colunas comuns: tabela com `column_name`, tipo em left, tipo em right.
### Apenas em <left_table>: lista de colunas.
### Apenas em <right_table>: lista de colunas.

## NÃO faça
- Não leia dados de linha das tabelas.
- Não compare conteúdo — apenas estrutura.
