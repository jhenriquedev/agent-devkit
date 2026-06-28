# Decision Rules: Generate Architecture Report

## Objetivo de decisao

Consolidar inventario, mapa de dependencias, lacunas e recomendacoes em
relatorio arquitetural para decisao humana.

## Entradas minimas

- `--inventory` deve apontar para inventario valido.
- `--dependency-map` deve ser usado quando ja existir; se ausente, pode ser
  derivado do inventario e declarado como derivado.
- `--output-dir` deve existir ou receber `--yes-create-dir`.

## Quando executar

Execute quando:

- o usuario precisa de uma visao consolidada da arquitetura AWS;
- inventario e dependencias ja foram coletados ou podem ser derivados
  localmente;
- a saida esperada e relatorio, resumo executivo, acoes recomendadas e perguntas
  abertas.

Nao execute quando:

- o inventario esta ausente;
- o usuario precisa de prova de seguranca, compliance ou auditoria profunda;
- faltam dados essenciais e o relatorio poderia ser interpretado como conclusao
  completa.

## Regras de consolidacao

1. Separar fatos coletados, inferencias, lacunas e perguntas abertas.
2. Nao esconder dependencias nao resolvidas.
3. Recomendacoes devem ser proximos passos de analise ou validacao, nao
   mutacoes diretas.
4. Resumo executivo deve mencionar escopo, conta, regiao e quantidade de
   recursos.
5. Limitar listagens longas em Markdown e preservar detalhes completos em JSON
   quando disponivel.
6. Nao incluir policies, secrets, tokens ou payloads brutos sensiveis.

## Criterios de qualidade

- `architecture-report.md` contem resumo, servicos, recursos-chave,
  dependencias e perguntas abertas.
- `executive-summary.md` e consistente com o inventario usado.
- `recommended-actions.md` prioriza lacunas e dependencias incertas.
- `open-questions.md` lista decisoes humanas pendentes.

## Escalacao

Pedir revisao humana quando:

- relatorio sera usado para aprovar mudanca em producao;
- ha lacunas em recursos criticos;
- dependencias inferidas sustentam recomendacao relevante.
