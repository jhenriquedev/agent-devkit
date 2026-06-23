# request-database-data

OBJETIVO: Montar um pedido de dados delegado a um agente de banco permitido e
executá-lo apenas sob pedido explícito do usuário.

ENTRADAS: --agent-id (obrigatório, allowlist: sqlserver-data-analyzer,
postgres-data-analyzer, azure-devops-orchestrator); --capability-id;
--request (texto ou query); --expected-schema (JSON); --execute;
--ai-devkit; --result-output.

RACIOCÍNIO:
1. Confirme que --agent-id está na allowlist (carregue source-routing.md +
   policies.yaml).
2. Por padrão (sem --execute): gere o pedido de delegação em .md descrevendo
   o que seria executado (read-only, sem efeito colateral).
3. Somente com --execute e pedido explícito do usuário: execute a delegação
   via CLI `ai-devkit run <agent-id> <capability-id> -- <args>`.
4. Valide o retorno contra o expected-schema antes de usar no workbook.

REGRAS DE DECISÃO:
- agent-id fora da allowlist: recuse imediatamente com mensagem clara.
- --execute sem pedido explícito do usuário: não execute; gere o .md de
  pedido e aguarde confirmação.
- Nunca mute sistemas de origem; operação é sempre somente leitura.

SAÍDA: delegation-request.md (sem --execute) ou resultado do agente delegado.

NÃO FAZER: conectar ao banco diretamente; executar sem pedido explícito;
mutar sistemas de origem.
