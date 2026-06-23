# Decision Rules: profile-table

## Rubrica de anomalias de coluna

| Condição | Severidade | Interpretação |
|---|---|---|
| `null_count == row_count` | Crítica | Coluna inutilizável; nunca preenchida |
| `null_count / row_count > 0.5` | Alta | Mais de 50% nulos; preenchimento irregular |
| `null_count / row_count > 0.1` | Média | Mais de 10% nulos; verificar obrigatoriedade |
| `distinct_count == 1` | Alta | Coluna constante (flag, default fixo, ou erro de carga) |
| `distinct_count == row_count` | Informativa | Candidato a chave única (verificar PK) |
| `distinct_count < 10` | Informativa | Baixa cardinalidade; candidato a categoria/enum |

## Regras de decisão

1. Sempre reportar anomalias críticas e altas primeiro.
2. O runner limita a 30 colunas — mencionar se truncado.
3. Não exibir dados brutos; apenas estatísticas agregadas.
4. Se `row_count == 0`: tabela vazia; avisar e não calcular taxas.
5. Separar observação (sintoma) de recomendação (próximo passo).

## Quando pedir info

- `schema` ou `table` ausente → pedir antes de executar.
