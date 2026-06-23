# ingest-dataset

## Objetivo
Inventariar a fonte de dados fixando rastreabilidade (sha256, row_count, formato,
amostras) antes de qualquer analise ou conclusao.

## Entradas
- `--source` (obrigatorio): caminho do arquivo (CSV, JSON, JSONL, XLSX, diretorio).
- `--sheet` (XLSX multi-aba): nome ou indice da aba.
- `--json-path` (JSON aninhado): chave/caminho para a lista de registros.
- `--max-rows`, `--sample-rows`, `--max-file-mb`: controles de custo de leitura.

## Raciocinio
1. Confirme que a fonte carregou: formato detectado, row_count vs
   original_row_count, truncated, warnings, sha256.
2. Se XLSX multi-aba sem --sheet ou JSON sem --json-path retornando 0/poucos
   registros: PARE e pergunte qual aba/lista usar antes de prosseguir.
3. Reporte formato, tamanho, colunas detectadas e amostras mascaradas de valores.
4. Registre sha256 como fingerprint da fonte para rastreabilidade downstream.

## Rubrica de decisao
- sha256 ausente -> resultado inutilizavel para decisao; bloqueie analise.
- truncated=true -> rotule "amostra parcial" em todas as conclusoes.
- warnings nao vazios -> liste-os explicitamente antes do resumo.
- XLSX multi-aba sem --sheet -> pergunte; nao adivinhe a aba.

## Saida
Resumo: formato, row_count, original_row_count, colunas (nome/tipo inferido),
amostras mascaradas de valores. Bloco "Rastreabilidade": fonte, sha256, truncado,
warnings.

## Nao fazer
- Nao exibir PII integral (CPF, CNPJ, email, telefone, nome) nas amostras.
- Nao concluir sobre a base sem sha256 registrado.
- Nao adivinhar aba/json-path; perguntar ao usuario.
