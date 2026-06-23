# Prompt: Correlate Azure Card Logs

## Objetivo
Usar o contexto de um card do Azure DevOps como contexto de busca e citar APENAS eventos
de log como evidência de correlação.

## Entradas esperadas
- Obrigatórias: `--source`, `--from`, `--to`.
- Opcionais: `--card-fixture` (JSON com `work_item`: id, title, tags), `--query`
  (sobrepõe a query derivada do card), `--service`, `--environment`, `--limit`.

## Raciocínio
1. Derive termos de busca do título + tags do card (ou use `--query` explícito).
2. Busque evidência no source e janela informados.
3. Avalie a força da correlação SOMENTE pelos eventos retornados, não pelo texto do card.

## Regras de decisão (confiança)
- "low": nenhum evento casou, ou só match textual fraco/genérico. Ver também: decision-rules.md.
- "medium": há eventos casando os termos do card na janela esperada.
- "high": eventos casam termo específico do card E um identificador (serviço/trace)
  coerente com o card. (Hoje o runner emite low/medium; trate "high" como avaliação sua.)
- Card é contexto, não prova.

## Formato de saída
Seções: Card Context (id/title/query), Log Evidence (source/eventos/tabela), Correlation
(confiança + justificativa baseada só em log).

## Não fazer
- Não tratar o texto do card como evidência.
- Não declarar correlação alta sem identificador coerente nos eventos.
