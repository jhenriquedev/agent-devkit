# Política de Runtime Node — Excel Workbook Builder

## Dependência

As capabilities de geração, preenchimento, render e aplicação de formulas
dependem do runtime Node externo com o pacote `@oai/artifact-tool`. O runtime
é resolvido na seguinte ordem de prioridade:

1. Variável de ambiente `CODEX_NODE` — caminho do executável `node`.
2. Variável de ambiente `CODEX_NODE_MODULES` — caminho da pasta `node_modules`
   com `@oai/artifact-tool`.
3. Variável de ambiente `NODE_MODULES` — caminho alternativo de `node_modules`.
4. Caminho padrão do runtime Codex: `~/.cache/codex-runtimes/`.

## Capabilities que dependem do runtime Node

- `create-template`
- `generate-workbook-from-data`
- `generate-workbook-from-template`
- `update-existing-workbook`
- `refresh-workbook-data`
- `add-formulas-and-validations`
- `run-workbook-operation`
- `create-pivot-summary`
- `create-summary-dashboard`
- `reconcile-datasets` (para geração do .xlsx de resultado)
- `generate-reconciliation-report`
- `create-adjustment-suggestions`
- `render-workbook-preview`

## Sinais de falha

Ao rodar qualquer capability acima, se aparecer nos logs:

- `"@oai/artifact-tool node_modules not found"`
- `"node executable not found"`

o runtime Node está ausente ou inacessível.

## Política de degradação (o que fazer quando Node está ausente)

1. **Aborte cedo** — não tente gerar o `.xlsx`; falhe rápido e reporte o gap.
2. **Entregue o que for possível sem Node:**
   - JSON normalizado (`ingest-*`, `normalize-tabular-data`)
   - Relatórios de validação em `.md` (`validate-source-data`)
   - Revisão/scan de workbooks existentes em `.md` (`review-generated-workbook`,
     `scan-formula-errors`) — esses runners são Python puro
   - Inspeção de templates (`inspect-template`) — Python puro
   - Lógica de conciliação sem o .xlsx de resultado (relatório .md)
   - Plano de workbook (`plan-workbook`) — Python puro
3. **Reporte explicitamente:**
   - Quais artefatos não puderam ser gerados e por quê.
   - Como instalar/configurar o runtime:
     ```
     # Defina as variáveis de ambiente antes de rodar:
     export CODEX_NODE=/caminho/para/node
     export CODEX_NODE_MODULES=/caminho/para/node_modules
     ```
4. **Nunca afirme ter gerado um `.xlsx`** sem que o arquivo exista no disco.

## Verificação prévia (pré-check)

Antes de chamar qualquer capability marcada como Node-dependente, verifique
a disponibilidade do runtime. A forma mais simples é tentar rodar
`inspect-template` (Python puro) e observar se erros de Node aparecem nos
logs antes mesmo da capability Node ser chamada. Alternativamente, tente uma
operação Node barata e trate o erro explicitamente.
