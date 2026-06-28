# Decision Rules: Invalidate CloudFront Cache

## Objetivo de decisao

Criar plano ou executar invalidation CloudFront com dry-run por padrao,
destacando custo, propagacao e impossibilidade de rollback direto.

## Entradas minimas

- `--distribution-id`, `--paths` e `--environment` sao obrigatorios.
- `resource_id` deve ser exatamente o distribution id.
- Execucao real exige `--execute`, `--confirm-resource <distribution-id>` e
  conta allowlisted.

## Quando executar

Execute em dry-run quando:

- o usuario quer revisar paths e distribuicao antes de invalidar cache;
- a distribuicao e os paths estao explicitos;
- o impacto de cache miss pode ser aceito.

Execute de fato apenas quando:

- o operador confirmou a distribuicao exata;
- a conta AWS foi validada;
- preflight `get-distribution` passou.

Nao execute quando:

- paths forem ambiguos;
- `/*` for usado sem confirmacao humana explicita;
- o usuario espera rollback imediato da invalidation.

## Regras de decisao

1. CloudFront e global; nao forcar region no comando de invalidation.
2. `/*` exige alerta de custo e potencial thundering herd.
3. Invalidation nao pode ser desfeita; rollback e aguardar propagacao ou
   publicar novo conteudo.
4. Em `prd`, destacar impacto em cache hit ratio e origem.
5. Conta fora da allowlist bloqueia antes da mutacao.

## Criterios de qualidade

- Dry-run mostra distribution id, paths e comando planejado.
- Execucao real gera validacao de conta, preflight, post-check e resultado.
- Relatorio nao omite que a acao nao tem rollback nativo.

## Escalacao

Pedir revisao humana quando paths incluem `/*`, a distribuicao serve producao ou
a origem pode nao suportar aumento temporario de trafego.
