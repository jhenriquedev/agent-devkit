# Contexto

- O N1 recebe `project` e `card` do Azure DevOps como entrada principal.
- A primeira acao sempre e ler o card completo com titulo, descricao,
  comentarios e anexos.
- O agente deve extrair CPF, proposta, contrato, telefone, e-mail, request id,
  correlation id e referencia TOPdesk quando existirem.
- O roteiro operacional prioriza CPF: base restritiva, BPO, Cognito,
  onboarding, proposta/contrato, logs e cards/chamados relacionados.
- Chamados de suporte ao cliente devem passar por roteamento de sintoma antes da decisao:
  login, onboarding, proposta/convenio/margem, restritivo, cartao ou financeiro.
- Regras de negocio ficam em `knowledge/domains/customer-support/` e devem ser
  carregadas sob demanda conforme a rota selecionada.
- Evidencias BPO devem ser coletadas via `bpo-analyser`; o N1 nao chama BPO
  diretamente.
- Escritas no Azure DevOps so podem ocorrer com `--execute`.
- A tag padrao de inicio de analise e `Analise N1`.
- O resultado deve separar fatos coletados, checks pendentes, inferencias e
  recomendacao.
