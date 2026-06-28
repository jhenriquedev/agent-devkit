# Decision Rules

- Classificar o sintoma usando `knowledge/domains/customer-support/symptom-routing.json` como fonte principal.
- Escolher uma rota dominante e listar aliases ou sinais que justificam a escolha.
- Quando o texto for ambiguo, retornar rota generica com checks minimos em vez de inventar dominio.
- Associar cada rota aos arquivos de knowledge e regras de negocio necessarios.
- Definir checks minimos antes de qualquer decisao de N1.
- Onboarding travado exige checar restritiva, BPO, Cognito/onboarding, proposta e logs quando houver erro temporal.
- Sintomas com erro, request id ou data/hora exigem busca de logs ou gap explicito.
- Nao expor CPF cru nos sinais de classificacao.
- Separar regras de negocio aplicaveis de recomendacoes operacionais.
- A rota deve alimentar `qualityGate` e `businessRulesApplied` do contrato N1.
