# Figma UI/UX Product Designer

Agente especialista em design de produto para aplicativos mobile e web. Ele
atua de forma agentic: descobre contexto, entrevista stakeholders, analisa
documentos/cards/projetos, define estrategia de design, cria ou evolui Figma,
revisa qualidade e entrega handoff para desenvolvimento.

## Modos De Operacao

- `direct_mcp`: Figma MCP bridge disponivel e ativado. O agente pode criar,
  editar, inspecionar e revisar arquivos Figma usando o bridge configurado.
- `local_mcp_bridge`: existe comando bridge, mas direct_mcp nao foi ativado.
- `plan_only`: sem MCP ou sem credenciais. O agente gera artefatos prontos para
  execucao humana ou para uma futura sessao com Figma conectado.
- `blocked`: a tarefa exige escrita real no Figma e o usuario marcou
  `--require-direct`, mas a integracao nao esta disponivel.

Credenciais ficam fora do repositorio, preferencialmente no ambiente local. O
`.env` pode apontar para um bridge, mas nao deve conter tokens versionados.

Direct mode pelo CLI exige:

```env
FIGMA_MCP_ENABLED=true
FIGMA_DIRECT_MODE=true
FIGMA_MCP_BRIDGE_COMMAND="figma-mcp-bridge"
FIGMA_DEFAULT_PLAN_KEY=
```

`FIGMA_ACCESS_TOKEN` sozinho nao habilita edicao completa de canvas. Criar e
editar frames exige MCP/plugin API por bridge ou runtime equivalente.

## Exemplos

```bash
agent capabilities figma-ui-ux-product-designer
agent run figma-ui-ux-product-designer setup-figma-mcp-bridge --install-bridge --write-env --login --validate-live --output-dir docs/figma-setup --yes-create-dir
agent run figma-ui-ux-product-designer ingest-design-source --source demanda.md --output-dir docs/design/ui --yes-create-dir
agent run figma-ui-ux-product-designer conduct-design-interview --brief demanda.md --output-dir docs/design/interview --yes-create-dir
agent run figma-ui-ux-product-designer create-web-app-design --brief demanda.md --output-dir docs/design/web --yes-create-dir
agent run figma-ui-ux-product-designer create-web-app-design --brief demanda.md --require-direct --yes-figma-write --figma-file-name "Portal" --output-dir docs/design/web --yes-create-dir
agent run figma-ui-ux-product-designer capture-url-to-figma --url http://localhost:3000 --figma-file-url https://figma.com/design/FILE/... --output-dir docs/design/capture --yes-create-dir
```

## Uso De Skills E Plugins

Antes de executar uma demanda, o agente deve consultar:

- `vendor/skills/CATALOG.md`
- `vendor/plugins/CATALOG.md`

Skills e plugins preferenciais:

- `vendor/skills/ecc/product-capability`
- `vendor/skills/ecc/frontend-patterns`
- `vendor/skills/ecc/brand-voice`
- `vendor/skills/drawio-diagramming`
- `vendor/plugins/open-design/open-design`

Quando Figma MCP estiver disponivel no ambiente, o agente deve seguir os fluxos
das skills Figma aplicaveis: `figma-create-new-file`, `figma-use`,
`figma-generate-design`, `figma-generate-library` e `figma-generate-diagram`.
No CLI local, esses fluxos sao executados por um bridge configurado em
`FIGMA_MCP_BRIDGE_COMMAND`.

## Artefatos

- `design-brief.md`
- `screen-inventory.md`
- `figma-action-plan.md`
- `design-system-spec.md`
- `mobile-screen-map.md`
- `web-screen-map.md`
- `facelift-plan.md`
- `feedback-triage.md`
- `journey-diagram.md`
- `dev-handoff.md`
- `design-quality-report.md`
- `figma-execution-result.json` quando houve execucao real
- `design-operation-log.md` quando houve execucao real
