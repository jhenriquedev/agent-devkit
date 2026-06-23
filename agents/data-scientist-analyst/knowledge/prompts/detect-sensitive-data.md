# detect-sensitive-data

## Objetivo
Identificar colunas com dados pessoais sensiveis (CPF, CNPJ, email, telefone,
nome) na base, reportando apenas exemplos mascarados, para decisao de
compartilhamento e conformidade.

## Entradas
- `--source` (obrigatorio): caminho do arquivo.
- `--sheet`, `--json-path`: seletores de sub-estrutura.
- `--max-rows`, `--max-file-mb`: controles de leitura.

## Raciocinio
1. Confirme carga: sha256, row_count, truncated, warnings.
2. Para cada coluna, aplique heuristicas de deteccao:
   CPF (formato 000.000.000-00 ou 11 digitos), CNPJ (14 digitos/formato),
   email (regex padrao), telefone (8-11 digitos com DDD), nome proprio
   (heuristica por padrao de texto).
3. Reporte has_sensitive_data (bool), categorias detectadas e colunas afetadas
   com exemplos mascarados (primeiros 3/ultimos 2 chars substituidos por *).
4. Quando has_sensitive_data=true, adicione aviso explicito de conformidade.

## Rubrica de decisao
- has_sensitive_data=true -> emita aviso antes de qualquer saida; mascare tudo.
- truncated=true -> deteccao e parcial; declare isso.
- Coluna ambigua (possivel nome/telefone) -> reporte como "suspeita" nao
  confirmada.

## Saida
Resultado bool (has_sensitive_data), tabela de colunas sensiveis (coluna,
categoria, exemplo_mascarado), aviso de conformidade se aplicavel, bloco de
rastreabilidade.

## Nao fazer
- Nao exibir nenhum dado PII integral — somente exemplos mascarados.
- Nao concluir "sem PII" em base truncada sem ressalva.
- Nao ignorar CNPJ na lista de mascaramento (inclui CPF, CNPJ, email, telefone,
  nome).
