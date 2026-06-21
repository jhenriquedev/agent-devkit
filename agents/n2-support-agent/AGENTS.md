# AGENTS.md

Instrucoes especificas para agentes trabalhando em `agents/n2-support-agent/`.

- Codigo, identificadores e nomes de capabilities ficam em ingles.
- Documentacao e runbooks ficam em portugues.
- O N2 nao deve repetir a triagem N1; deve partir do handoff N1, card ou
  evidencias existentes para investigar causa raiz.
- O N2 pode usar Azure DevOps para ler, comentar, anexar artefatos, taguear e
  mover cards, mas essas operacoes sao automacao de apoio.
- O artefato `patch_plan.md` e a entrega central quando houver plano de
  correcao. Se `--output` for informado, grave nesse path. Se card Azure for
  informado sem `--output`, prepare/anexe ao card conforme `--execute`.
- Mutacoes externas exigem `--execute`.
