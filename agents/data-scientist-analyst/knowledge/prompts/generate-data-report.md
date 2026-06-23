# generate-data-report

## Objetivo
Gerar relatorio markdown de perfil da base (qualidade, schema, PII, warnings)
a partir de profile-dataset, com rastreabilidade completa.

## Entradas
- `--source` (obrigatorio): caminho da base ou JSON de profile-dataset.
- `--output` (obrigatorio): caminho do arquivo markdown a gerar.
- `--sheet`, `--json-path`: seletores de sub-estrutura.
- `--max-rows`, `--max-file-mb`: controles de leitura.

## Raciocinio
1. Garanta que profile-dataset foi executado (sha256, row_count, quality, columns,
   sensitive_data presentes).
2. Monte relatorio com secoes: Cabecalho (fonte, sha256, data), Sumario de
   Qualidade, Schema por Coluna, Dados Sensiveis (mascarado), Warnings, Proximos
   Passos.
3. Mascare PII em todos os exemplos.
4. Destaque quality_score e colunas criticas de qualidade.

## Rubrica de decisao
- sha256 ausente -> relatorio nao auditavel; bloqueie.
- has_sensitive_data=true -> secao de PII obrigatoria com aviso de conformidade.
- truncated=true -> declare "relatorio de amostra" no cabecalho.
- Relatorio so gerado com --output.

## Saida
Arquivo markdown em --output: cabecalho (fonte, sha256, linhas, data), sumario
de qualidade, tabela de schema, secao de PII mascarada, warnings, recomendacoes.
Confirme path gerado.

## Nao fazer
- Nao gerar relatorio sem --output.
- Nao exibir PII integral no relatorio.
- Nao reportar relatorio como completo sem quality_score.
