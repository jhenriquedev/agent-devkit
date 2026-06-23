# AWS Dependency Map

> Contrato de saida: capability `map-service-dependencies`

## Resumo
- **Nodes (recursos):** N
- **Arestas (dependencias):** N
- **Dependencias nao resolvidas:** N

## Arestas Mapeadas
| Source | Target | Tipo | Confianca | Evidencia |
|---|---|---|---|---|
| `{source_id}` | `{target_id}` | `{type}` | `confirmed\|inferred` | `{evidence}` |

## Dependencias Nao Resolvidas
Arestas cujo target nao existe no inventario e nao e um ARN valido:
| Source | Target | Tipo | Confianca |
|---|---|---|---|
| `{source_id}` | `{target_id}` | `{type}` | `{confidence}` |

> AVISO: dependencias nao resolvidas indicam que o mapa pode estar INCOMPLETO.
> Recursos fora do escopo coletado ou em outras regioes/contas podem nao aparecer.

---
*FATOS: arestas com confianca `confirmed` (campo direto da AWS API).*
*INFERENCIAS: arestas com confianca `inferred` (deduzidas por convencao/nome).*
*LACUNAS: dependencias `unresolved` — targets desconhecidos.*

