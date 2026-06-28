# Decision Rules: Map Service Dependencies

## Objetivo de decisao

Gerar um mapa de dependencias a partir de `inventory.json`, preservando a
diferenca entre relacionamentos confirmados, inferidos e nao resolvidos.

## Entradas minimas

- `--inventory` deve apontar para um `inventory.json` valido.
- O inventario deve conter `resources` normalizados.
- `--output-dir` deve existir, ou a execucao deve receber `--yes-create-dir`.

## Quando executar

Execute quando:

- o usuario precisa entender dependencias entre workloads AWS;
- `generate-architecture-report` ou `estimate-blast-radius` precisa de um mapa
  explicito;
- ha relacoes em `relationships` dos recursos coletados.

Nao execute quando:

- o inventario nao existir ou estiver vazio sem explicacao;
- o usuario precisa de chamada AWS adicional para preencher lacuna de coleta;
- a pergunta for sobre permissao IAM profunda, pois isso pertence a auditoria de
  seguranca.

## Regras de dependencia

1. Toda edge deve manter `source_id`, `target_id`, `type`, `confidence` e
   `evidence` quando disponivel.
2. Usar `confirmed` apenas quando a relacao veio de campo direto da API AWS.
3. Usar `inferred` para heuristicas, convencoes de nome ou relacoes sem campo
   direto.
4. Enviar targets fora do inventario e nao resolvidos para
   `unresolved-dependencies.json`.
5. Nao remover dependencias incertas para deixar o mapa "limpo"; incerteza e
   parte do resultado.
6. Nao promover ARN externo a dependencia segura sem indicar que o alvo pode
   estar fora do escopo coletado.

## Criterios de qualidade

- `dependency-map.json` contem `nodes`, `edges`, `edge_count`,
  `unresolved_dependencies` e `unresolved_count`.
- `dependency-map.md` mostra arestas com tipo e confianca.
- Dependencias nao resolvidas sao contadas e exportadas separadamente.
- O relatorio humano deixa claro quando o impacto pode estar subestimado.

## Escalacao

Pedir nova coleta ou ampliar escopo quando:

- muitas dependencias ficam nao resolvidas;
- edges criticas para producao aparecem apenas como `inferred`;
- o recurso alvo de uma analise downstream nao aparece no mapa nem no inventario.
