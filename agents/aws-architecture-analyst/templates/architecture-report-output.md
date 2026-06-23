# AWS Architecture Report

> Contrato de saida: capability `generate-architecture-report`

## Resumo Executivo
- **Account:** `{account_id}`
- **Region:** `{region}`
- **Fonte:** `real | fixture`
- **Total de recursos:** N
- **Dependencias mapeadas:** N arestas (N nao resolvidas)

## Servicos Inventariados
| Servico | Recursos |
|---|---|

## Recursos-Chave
Recursos com maior numero de dependentes ou criticidade inferida:
| Nome | Servico | Dependentes Diretos | Observacao |
|---|---|---|---|

## Dependencias Mapeadas
Arestas principais com confianca:
| Source | Target | Tipo | Confianca |
|---|---|---|---|

## Achados Consolidados
Findings das reviews executadas (resilience / observability / networking):
| Severidade | Categoria | Mensagem |
|---|---|---|

## Acoes Recomendadas
Acoes para validacao humana — nao mutacoes diretas:
1. Revisar dependencias com baixa confianca antes de qualquer mudanca.
2. Completar tags de ownership, ambiente e criticidade.
3. Validar dependencias nao resolvidas.
4. ...

## Perguntas Abertas e Lacunas
- Quais workloads sao criticos para producao?
- Quais recursos possuem owners definidos?
- Existem dependencias externas fora da conta AWS inventariada?
- Servicos do escopo MVP nao coletados: `{lista}`

---
*FATOS: dados retornados diretamente pela AWS API ou fixture.*
*INFERENCIAS: relacoes e conclusoes deduzidas dos dados — rotuladas com confianca.*
*LACUNAS: informacoes ausentes ou servicos nao coletados — listados acima.*

