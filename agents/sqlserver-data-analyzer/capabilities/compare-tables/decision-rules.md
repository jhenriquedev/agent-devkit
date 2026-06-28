# Decision Rules: Compare Tables

- Comparar tabelas por metadados, contagens e amostras read-only limitadas.
- Validar database, schema, tabela e colunas antes de consultar.
- Separar diferencas de coluna, tipo, nulabilidade, chave, indice e volume estimado.
- Nao executar sincronizacao, merge, insert, update ou delete.
- Mascarar valores pessoais quando comparacao exigir amostra.
- Preferir chaves declaradas; sem chave, declarar baixa confianca.
- Aplicar `TOP`, timeout e `LOCK_TIMEOUT` em qualquer amostra.
- Registrar direcao da comparacao para evitar confundir `left_only` e `right_only`.
- Sugerir proximos checks sem propor alteracao destrutiva.
- Bloquear comandos de escrita e `MERGE`, mesmo em comparacoes.
