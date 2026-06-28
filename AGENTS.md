# AGENTS.md

Contrato raiz para agentes de IA (Claude Code, Codex, Cursor e qualquer agente
compativel com o padrao [AGENTS.md](https://agents.md)). Este arquivo e a fonte
de instrucoes que todo agente deve ler antes de trabalhar neste repositorio.

> Para subprojetos, um `AGENTS.md` mais especifico pode ser colocado na pasta
> correspondente. O arquivo mais proximo na arvore de diretorios tem
> precedencia.

## Sobre este projeto

O **Agent DevKit** e uma biblioteca de agentes especialistas, capabilities,
prompts, repositories, MCPs, templates e conhecimento operacional para
desenvolvimento e sustentacao de software com IA.

O produto principal do repositorio sao agentes pre-criados e versionados em
`agents/<agent-id>/`. Cada agente encapsula uma inteligencia especializada e
expoe capabilities prontas para uso por Codex, Claude, Cursor ou outro agente
compativel.

## Como trabalhar aqui

1. **Spec antes de codigo.** Para qualquer mudanca nao trivial, alinhe contrato,
   capability, entradas, saidas e quality gates antes da implementacao.
2. **Agente antes de pasta generica.** Se a mudanca pertence a um dominio ou
   capacidade especifica, coloque-a em `agents/<agent-id>/`.
3. **Capability como unidade executavel.** Casos de uso devem viver em
   `agents/<agent-id>/capabilities/<capability-id>/`.
4. **Infra executavel.** Acesso externo deve ficar em repositories dentro de
   `agents/<agent-id>/infra/integrations/<provider>/`.
5. **Raiz minima.** So mantenha na raiz o que for global ao repositorio inteiro.
6. **Contexto sob demanda.** Manifests e `knowledge/context.md` devem ser
   pequenos; detalhes ficam nos arquivos carregados pela capability.
7. **Mudancas incrementais e revisaveis.** Prefira passos pequenos, testaveis e
   com escopo claro.

## Estrutura raiz

- `.github/`: governanca GitHub, workflows, templates de issue/PR e CODEOWNERS.
- `agents/`: agentes especialistas e suas capabilities.
- `cli/`: documentacao da CLI do DevKit; o executavel canonico fica na raiz
  como `agent`. `ai-devkit` e `aikit` sao aliases legados de compatibilidade.
- `providers/`: registry global dos providers usados pelo runtime.
- `plugins/`: adaptadores nativos finos para hosts como Codex App e Claude Code.
- `vendor/`: skills, plugins e bundles externos/importados.
- `scripts/`: automacoes operacionais globais do repositorio.

A pasta `docs/` e local, usada para desenvolvimento do projeto e artefatos
gerados. Ela e ignorada pelo Git e nao representa documentacao versionada do
projeto final.

## Estrutura de agentes

Um agente deve concentrar sua propria superficie publica e implementacao:

```text
agents/<agent-id>/
├─ AGENTS.md
├─ README.md
├─ agent.yaml
├─ capabilities/
├─ knowledge/
├─ templates/
└─ infra/
```

- `capabilities/`: front externo do agente, com casos de uso acionaveis.
- `knowledge/`: contexto, politicas e regras necessarias para a tomada de
  decisao do agente.
- `templates/`: modelos de arquivos, respostas e artefatos gerados pelas
  capabilities.
- `infra/`: repositories, models e CLIs que conectam o agente a sistemas
  externos.

## Convencoes

- **Nomes de pastas/arquivos:** `kebab-case`.
- **Documentacao e specs:** Markdown, em portugues.
- **Manifesto de agente:** `agents/<agent-id>/agent.yaml`.
- **Manifesto de capability:**
  `agents/<agent-id>/capabilities/<capability-id>/capability.yaml`.
- **Acesso externo:** usar repository em `infra/integrations/<provider>/`, nao
  scripts soltos.
- **ADRs:** registrar em local versionado quando uma decisao for dificil de
  reverter.

## Guardrails

- **Nunca commitar segredos** (chaves, tokens, `.env`, credenciais).
- Nao introduzir dependencias ou servicos externos sem registrar a decisao.
- Nao alterar arquivos ou escopo alem do que foi solicitado.
- Em caso de ambiguidade, perguntar antes de assumir.

## Skills e plugins ativos

Este repositorio disponibiliza skills e plugins externos em `vendor/`. Eles
carregam sob demanda: antes de uma tarefa, consulte o catalogo e carregue apenas
o recurso cuja `description` casa com o trabalho.

- **Catalogo de skills:** [`vendor/skills/CATALOG.md`](vendor/skills/CATALOG.md).
- **Catalogo de plugins:** [`vendor/plugins/CATALOG.md`](vendor/plugins/CATALOG.md).

Regra de roteamento: ao receber uma tarefa, escolha primeiro o agente ou
capability mais especifico. Use `vendor/` apenas quando a tarefa exigir uma
skill ou plugin externo.

### napkin

Em toda sessao, antes de qualquer trabalho, leia e siga
[`vendor/skills/napkin/SKILL.md`](vendor/skills/napkin/SKILL.md). Mantenha o
runbook em `vendor/skills/napkin/napkin.md`. Aplique o que estiver la
silenciosamente.

## Estado atual

Fundacao inicial do projeto. A arquitetura alvo e uma biblioteca de agentes
especialistas em `agents/`, com capabilities autocontidas e repositories de
integracao dentro de cada agente.
