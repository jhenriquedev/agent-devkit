# Rubricas de Decisao — AWS Architecture Analyst

Este arquivo define as rubricas de confianca e severidade usadas pelos prompts
de review e blast radius. Referenciado por: review-resilience, review-observability,
review-networking, estimate-blast-radius.

---

## 1. Rubrica de Confianca (dependencias)

| Nivel | Significado | Quando usar |
|---|---|---|
| `confirmed` | Campo direto retornado pela AWS (ex.: Lambda Role, VpcConfig) | Relacao visivel em um atributo da API AWS |
| `inferred` | Deduzida por convencao de nome, padrao ou heuristica | Nomeclatura sugere relacao, mas nao foi lida de um campo da API |
| `unresolved` | Target fora do inventario e nao-ARN | Recurso provavelmente fora do escopo coletado |

Regra: nunca promova `inferred` a `confirmed` sem evidencia da API. `unresolved`
indica que o mapa pode estar incompleto — declare explicitamente.

---

## 2. Rubrica de Severidade (reviews)

| Nivel | Significado | Exemplos |
|---|---|---|
| `high` | Exposicao publica inesperada de recurso sensivel; recurso critico sem redundancia/backup confirmados | Recurso de dados publicamente acessivel; instancia critica sem backup |
| `medium` | Risco concreto que precisa de validacao | EC2 com IP publico; SQS sem DLQ; ausencia total de alarms; SG com 0.0.0.0/0 em porta administrativa |
| `info` | Configuracao a validar — pode ser esperada | Lambda sem VPC (pode ser intencional); retention de logs generosa |
| `gap` | Atributo necessario para a avaliacao nao foi coletado | `has_dlq` ausente; `public_ip` nao coletado pelo collector |

### Regra critica para `gap`
Um finding do tipo `gap` NUNCA deve ser interpretado como "ok" ou "sem risco".
Significa que os dados necessarios para avaliar o risco nao estao disponiveis.
O finding de gap deve sempre incluir:
- Qual atributo esta faltando
- Qual capability de coleta precisaria ser executada para preencher a lacuna
- Se a avaliacao continua sem o dado, ou deve ser pausada

---

## 3. Regras de Blast Radius

- Dependentes com arestas `inferred` tem incerteza maior — marcar no artefato.
- Se houver `unresolved_dependencies` relacionadas ao recurso alvo, declarar
  explicitamente: "impacto pode estar SUBESTIMADO".
- Recurso alvo nao encontrado no inventario: PARAR e reportar erro — nao
  retornar blast radius vazio como se fosse seguro.

---

## 4. Quando parar e pedir informacao

| Situacao | Acao |
|---|---|
| Region faltando para servico regional na coleta real | Parar e pedir region ao usuario |
| inventory.json ausente para capability downstream | Parar e indicar que discover-account-inventory deve ser executado primeiro |
| resource_id do blast radius nao existe no inventario | Parar e reportar recurso nao encontrado |
| Exposicao critica detectada | Sinalizar ao humano antes de prosseguir |

---

## 5. Criterios de qualidade (quality_gates)

Criterios de `knowledge/policies.yaml` que toda execucao deve satisfazer:

1. `aws_scope_recorded`: profile, account, region e filtros registrados em collection-metadata.json
2. `read_only_allowlist_enforced`: nenhum comando fora da ALLOWED_COMMANDS executado
3. `inventory_json_valid`: inventory.json gerado com campos obrigatorios (account_id, region, resources, gaps)
4. `dependency_confidence_recorded`: toda aresta tem campo `confidence` preenchido
5. `facts_inferences_and_gaps_separated`: toda saida separa FATOS / INFERENCIAS / LACUNAS
