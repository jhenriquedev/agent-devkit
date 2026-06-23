# profile-dataset

## Objetivo
Gerar perfil estatistico completo (qualidade, distribuicao, chaves provaveis,
PII), separando fatos observados de inferencias, para decisao sobre analises
subsequentes.

## Entradas
- `--source` (obrigatorio): caminho do arquivo (CSV, JSON, JSONL, XLSX).
- `--sheet` (XLSX): aba alvo.
- `--json-path` (JSON aninhado): caminho para lista.
- `--max-rows`, `--sample-rows`, `--max-file-mb`: controles de leitura.
- `--output`: gravar JSON de perfil em disco.

## Raciocinio
1. Confirme carga completa: sha256, row_count, original_row_count, truncated,
   warnings — declare-os antes de qualquer estatistica.
2. Se XLSX multi-aba sem --sheet ou JSON aninhado sem --json-path com poucos
   registros: PARE e pergunte.
3. Para cada coluna: tipo, nulos, unicos, min/max/mean/median (numericas),
   top-valores, chave provavel.
4. Avalie qualidade global (quality_score) e sinalize colunas criticas.
5. Verifique sensitive_data.has_sensitive_data e categorias detectadas; se true,
   avise antes de compartilhar.

## Rubrica de decisao
- sha256 ausente -> bloqueie uso do perfil para decisao.
- truncated=true -> todo resultado e "amostra parcial"; rotule.
- has_sensitive_data=true -> aviso obrigatorio antes de compartilhar artefato.
- quality.quality_score ausente -> perfil incompleto; nao use para modelagem.

## Saida
Secoes: Rastreabilidade (fonte, sha256, linhas, truncamento, warnings),
Schema/Qualidade (tabela por coluna), Resumo de PII (mascarado), Inferencias
destacadas separadas de fatos.

## Nao fazer
- Nao exibir PII integral (CPF/CNPJ/email/telefone/nome).
- Nao concluir sem profile completo.
- Nao adivinhar aba/json-path sem perguntar.
