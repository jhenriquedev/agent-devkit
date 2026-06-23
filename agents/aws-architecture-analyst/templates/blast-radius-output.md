# Blast Radius

> Contrato de saida: capability `estimate-blast-radius`

## Recurso Alvo
- **ID:** `{resource_id}`
- **Nome:** `{resource_name}`
- **Servico:** `{service}`

## Dependentes Diretos
Recursos que dependem diretamente do recurso alvo (arestas diretas no grafo reverso):
| ID | Nome | Servico | Confianca da Aresta |
|---|---|---|---|

**Total diretos:** N

## Dependentes Indiretos
Recursos afetados transitivamente:
| ID | Nome | Servico |
|---|---|---|

**Total indiretos:** N

## Incertezas
- Dependentes via arestas `inferred` tem incerteza maior.
- Dependencias `unresolved` podem indicar impacto SUBESTIMADO.
- Recursos fora do escopo coletado podem nao aparecer neste grafo.

## Acoes Inseguras
- Alterar ou remover o recurso alvo sem validar todos os dependentes diretos.
- Assumir impacto baixo quando existem dependencias nao resolvidas em aberto.

---
*FATOS: dependentes com aresta `confirmed`.*
*INFERENCIAS: dependentes com aresta `inferred`.*
*LACUNAS: dependencias `unresolved` — impacto pode estar subestimado.*

