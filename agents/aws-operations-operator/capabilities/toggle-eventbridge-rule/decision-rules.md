# Decision Rules: Toggle EventBridge Rule

## Objetivo de decisao

Habilitar ou desabilitar uma regra EventBridge de forma controlada, com dry-run
por padrao e rollback pela acao oposta.

## Entradas minimas

- `--rule-name`, `--action` e `--environment` sao obrigatorios.
- `--action` deve ser `enable` ou `disable`.
- `resource_id` deve ser exatamente o nome da regra.
- Execucao real exige `--execute`, `--confirm-resource <rule-name>` e conta
  allowlisted.

## Quando executar

Execute em dry-run quando:

- o usuario quer pausar ou reativar agendamento/triggers;
- a regra e a acao estao explicitas;
- o impacto do schedule foi considerado.

Execute de fato apenas quando:

- preflight `describe-rule` passou;
- o operador confirmou a regra exata;
- a conta AWS foi validada.

Nao execute quando:

- action estiver fora de `enable|disable`;
- a regra controla cobranca, compliance ou processamento critico sem aprovacao;
- o usuario nao entende o efeito de pausar ou reativar triggers.

## Regras de decisao

1. `disable` pausa agendamentos/triggers; `enable` reativa.
2. Rollback e executar a acao oposta.
3. Em `prd`, destacar efeito de pausar jobs criticos.
4. Action invalida deve falhar antes de qualquer plano.
5. Conta fora da allowlist bloqueia antes da mutacao.

## Criterios de qualidade

- Dry-run mostra rule, action, comando e rollback hint.
- Execucao real gera validacao de conta, preflight, post-check e resultado.
- Relatorio final deixa claro se a regra ficou enabled ou disabled quando o
  post-check trouxer esse estado.

## Escalacao

Pedir revisao humana quando a rule estiver associada a pagamentos, limpeza de
dados, conciliacao, compliance, notificacoes criticas ou integracoes externas.
