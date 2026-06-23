# Prompt: build-analysis-query

## OBJETIVO
Montar um SELECT seguro e pronto para revisão a partir de schema, tabela e
colunas selecionadas. Não executa a query.

## ENTRADAS
- `schema` (obrigatório): schema da tabela.
- `table` (obrigatório): nome da tabela.
- `columns` (opcional): lista separada por vírgula; se omitida, usa `*`.
- `limit` (opcional, default 100).
- `--question` (argumento declarado mas não processado pelo runner): se o
  usuário fizer uma pergunta em linguagem natural, o host (você) deve
  traduzir a pergunta em `schema`/`table`/`columns` antes de chamar esta
  capability. Informe ao usuário que tradução NL→SQL não é automática aqui.

## RACIOCÍNIO (passos)
1. Se `--question` for recebido, traduza a pergunta para os parâmetros
   `schema`, `table` e `columns` usando conhecimento do banco já descoberto.
   Informe ao usuário a tradução feita.
2. Execute a capability `build-analysis-query --schema <s> --table <t>`.
3. Leia `query` e `notes[]`.
4. Avise que a query deve ser revisada antes de executar (filtros, JOINs).

## RUBRICA / REGRAS DE DECISÃO
- Argumento `--question` não é processado automaticamente pelo runner; o
  host deve fazer a tradução. Deixe isso claro ao usuário.
- Se a pergunta não puder ser traduzida com informações disponíveis, chame
  `describe-table` antes.
- A query gerada usa TOP e schema/table com `quote_ident` — é segura para
  `run-readonly-query` diretamente.

## SAÍDA
Bloco SQL + nota "revise filtros e JOINs antes de executar via
`run-readonly-query`".

## NÃO FAÇA
- Não execute a query nesta capability.
- Não gere DML (INSERT/UPDATE/DELETE) mesmo que seja "só um exemplo".
- Não prometer NL→SQL automático via `--question` no runner.
