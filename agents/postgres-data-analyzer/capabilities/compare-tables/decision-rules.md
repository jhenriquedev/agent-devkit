# Decision Rules: Compare Tables

- Comparar tabelas apenas por metadados, contagens e amostras read-only limitadas.
- Validar schema e nomes das duas tabelas antes de consultar.
- Separar diferencas de coluna, tipo, nulabilidade, chave e volume estimado.
- Nao executar sincronizacao, merge, insert, update ou delete.
- Mascarar valores pessoais quando a comparacao exigir amostra de linhas.
- Preferir chaves declaradas para comparacao; sem chave, declarar baixa confianca.
- Registrar direcao da comparacao para evitar confundir `left_only` e `right_only`.
- Sugerir proximos checks sem propor alteracao destrutiva.
