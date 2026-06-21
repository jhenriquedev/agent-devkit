# Workflow

Classificar o sintoma do cliente com base no knowledge operacional
MeuCashCard.

## Entradas

- `--text`: texto livre do chamado, card ou comentario.
- `--fixture`: fixture com `text`, `work_item` ou `card`.
- `--format json`: contrato estruturado para consumo por outro agente.

## Saida

Retorna:

- `routeId`;
- dominio;
- aliases encontrados;
- arquivos de knowledge recomendados;
- checks minimos;
- regras de negocio relevantes;
- quality gate do N1;
- lacunas iniciais.
