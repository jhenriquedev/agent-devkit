# Regras

- Inspecionar a fonte e confirmar profile antes de gerar artefatos.
- Exigir `--yes-create-dir` quando `output_dir` nao existir e `--yes-overwrite` para sobrescrever.
- Nunca persistir segredos brutos, tokens, senhas, cookies, certificados, private keys, connection strings ou payloads pessoais completos.
- Separar cada item gerado como `fact`, `inference` ou `gap`, com evidencia e source rastreavel.
- Usar paths relativos ao source root ou `repo://<project-id>/...`; nao gravar paths absolutos.
- Rodar ou recomendar `validate-knowledge` e corrigir ate a pasta ficar validavel.
