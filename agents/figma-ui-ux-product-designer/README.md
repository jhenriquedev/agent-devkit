# Figma UI/UX Product Designer

Agente especialista em design de produto para aplicativos mobile e web. Ele
atua de forma agentic: descobre contexto, entrevista stakeholders, analisa
documentos/cards/projetos, define estrategia de design, cria ou evolui Figma,
revisa qualidade e entrega handoff para desenvolvimento.

## Modos De Operacao

- `direct`: Figma MCP/conector disponivel e configurado. O agente pode criar e
  editar arquivos Figma usando as ferramentas do ambiente.
- `plan_only`: sem MCP ou sem credenciais. O agente gera artefatos prontos para
  execucao humana ou para uma futura sessao com Figma conectado.
- `blocked`: a tarefa exige escrita real no Figma e o usuario marcou
  `--require-direct`, mas a integracao nao esta disponivel.

Credenciais ficam fora do repositorio, preferencialmente em `.env`.

## Exemplos

```bash
./ai-devkit capabilities figma-ui-ux-product-designer
./ai-devkit run figma-ui-ux-product-designer ingest-design-source --source demanda.md --output-dir docs/design/ui --yes-create-dir
./ai-devkit run figma-ui-ux-product-designer conduct-design-interview --brief demanda.md --output-dir docs/design/interview --yes-create-dir
./ai-devkit run figma-ui-ux-product-designer create-web-app-design --brief demanda.md --output-dir docs/design/web --yes-create-dir
./ai-devkit run figma-ui-ux-product-designer capture-url-to-figma --url http://localhost:3000 --figma-file-url https://figma.com/design/FILE/... --output-dir docs/design/capture --yes-create-dir
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
