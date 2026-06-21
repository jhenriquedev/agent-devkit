# Customer Onboarding Triage

Runbook operacional N1 para casos de onboarding, proposta, bloqueio por CPF e
falhas relacionadas ao cliente.

## Ordem deterministica

1. Ler card Azure DevOps.
2. Extrair entidades do titulo, descricao, comentarios e anexos.
3. Classificar sintoma usando `knowledge/domains/meucashcard/symptom-routing.json`.
4. Carregar regras de negocio do dominio selecionado.
5. Se houver CPF, consultar base restritiva e classificar como `hit`, `clear`
   ou `unavailable`.
6. Se houver CPF/proposta, consultar BPO para situacao da proposta,
   formalizacao, observacoes e documentos anexados.
7. Se houver CPF, consultar situacao do usuario no Cognito.
8. Se houver CPF/proposta, consultar onboarding.
9. Se houver proposta/contrato, consultar status de proposta e contrato.
10. Buscar logs por CPF, proposta, request id ou correlation id.
11. Verificar chamados TOPdesk e cards relacionados quando houver referencia.
12. Decidir: resolvido N1, pedir informacao, escalar N2 ou manter em analise.
13. Gerar comentario interno, resposta ao solicitante e pacote de escalonamento.

## Criterios de parada

- Sem CPF, proposta, contrato ou referencia tecnica: pedir informacoes minimas.
- CPF em base restritiva ativa: orientar ou escalar conforme politica do time.
- Base restritiva indisponivel: nao assumir CPF liberado; manter check como
  pendente operacional ou escalar com evidencia da indisponibilidade.
- Sintoma de convenio/margem: sempre verificar convenio, fonte da margem e
  regra de percentual antes de concluir divergencia.
- Sintoma de proposta, formalizacao, CCB ou margem: consultar BPO antes de
  concluir falha interna ou bug de app.
- Sintoma de onboarding: sempre derivar etapa atual por evolutions e separar
  etapa foreground, background job e integracao externa.
- Cognito desabilitado ou nao confirmado: indicar acao operacional de conta.
- Erro tecnico com logs relevantes: escalar N2 com evidencias.
- Evidencia insuficiente: pedir informacao objetiva, nao inferir causa.
