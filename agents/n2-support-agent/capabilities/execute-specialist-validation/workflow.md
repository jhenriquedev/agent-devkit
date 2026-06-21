# Execute Specialist Validation

Planeja ou executa validacoes especialistas para confirmar ou descartar a
hipotese N2.

## Entradas

- `--project` e `--card`: contexto Azure usado para rastreabilidade.
- `--n1-contract`: contrato N1 com entidades e evidencias ja triadas.
- `--codebase-path`: projeto analisado para classificar a causa raiz.
- `--fixture`: dados locais para teste sem rede.
- `--execute`: executa validacoes com contrato seguro.
- `--format json`: retorna contrato estruturado.

## Comportamento

Sem `--execute`, a capability retorna validacoes planejadas com
`commandPreview`. Com `--execute`, ela chama o agente especialista quando houver
parametros suficientes e seguros. Nesta versao, a execucao direta cobre BPO por
numero de proposta; banco e logs continuam como validacoes planejadas quando a
capability nao tiver uma query ou janela temporal segura.

## Saida

Cada validacao retorna `agent`, `capability`, `status`, `reason`,
`commandPreview` e `resultSummary`. Status possiveis:

- `planned`: validacao selecionada, mas nao executada.
- `executed`: validacao executada pelo agente especialista.
- `failed`: tentativa de execucao falhou.
- `skipped`: nao ha contrato executavel seguro para essa validacao.
