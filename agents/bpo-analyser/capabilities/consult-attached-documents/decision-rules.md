# Regras

- Nao imprimir `ArquivoBase64` por padrao.
- `--include-content` deve ser usado apenas quando o operador precisa do
  conteudo bruto.
- Nao chamar alvos configurados em `BPO_FORBIDDEN_URL_PATTERNS`.
- Tratar conteudo binario como dado sensivel e nao interpretar seu conteudo.
