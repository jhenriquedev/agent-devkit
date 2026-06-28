# Decision Rules

- Construir estrategia de reproducao antes de qualquer plano de implementacao.
- Selecionar o primeiro arquivo candidato confiavel e inferir o teste mais proximo.
- Formular `given`, `when` e `then` a partir de evidencias N1/N2, nao de suposicoes.
- Incluir passo RED que falhe pelo comportamento observado no suporte.
- Incluir passo GREEN limitado ao menor ajuste capaz de corrigir o comportamento.
- Incluir passo REFACTOR somente depois do teste verde.
- Se nao houver arquivo ou sintoma reproduzivel, registrar pergunta bloqueante.
- Nao sugerir teste que dependa de dados reais de cliente, CPF cru ou ambiente produtivo.
- Cobrir migrations, jobs e integrações apenas quando forem parte direta da causa provavel.
- A estrategia deve ser reutilizavel dentro do `patch_plan.md`.
