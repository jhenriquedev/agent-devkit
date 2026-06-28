# Decision Rules

- Carregar fixture, contrato N1 ou card Azure sem repetir triagem N1 por padrao.
- Preferir `n1_contract` estruturado quando existir; usar card para complementar contexto.
- Extrair entidades, sintoma, evidencias, checks e diagnostic gaps para um contrato N2 unico.
- Se N1 estiver ausente ou incompleto, marcar necessidade de rerun N1 em vez de inventar checks.
- Mascarar CPF e reduzir dados pessoais de titulo, descricao e comentarios.
- Preservar ids tecnicos, proposta, contrato, request id e correlation id quando necessarios para N2.
- Registrar se o card Azure e o contrato N1 foram carregados.
- Nao executar mutacoes Azure nem escrever `patch_plan.md`.
- Diferenciar evidencias objetivas de hints ou observacoes livres.
- A saida deve ser consumivel por todas as demais capabilities N2.
