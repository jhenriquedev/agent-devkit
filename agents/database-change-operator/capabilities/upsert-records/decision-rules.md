# Decision Rules

- Entrada deve ser JSON ou CSV.
- Todas as colunas devem ter identificadores SQL simples.
- A coluna chave precisa existir no dataset.
- Use para cargas pequenas e controladas, nao para ETL massivo.
- Sem `--execute`, retornar dry-run com `record_count` e plano.
- Respeitar `max_affected_rows`; volumes acima do limite exigem confirmacao reforcada.
- Registrar execucoes reais em `ai_devkit_write_audit`.
