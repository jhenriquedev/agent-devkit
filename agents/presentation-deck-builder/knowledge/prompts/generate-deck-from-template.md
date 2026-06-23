# Prompt: generate-deck-from-template

## OBJETIVO
Gerar o deck .pptx (+ preview .png + layout.json) a partir de template validado
e input estruturado, com pre-check da dependencia externa.

## ENTRADAS
- `--template-id` (obrigatorio): identificador do template.
- `--input` (obrigatorio): arquivo JSON ou Markdown de relatorio.
- `--template-version` (opcional): versao; default = current_version.
- `--templates-root` (opcional): diretorio raiz.
- `--output` (opcional): caminho do deck de saida.

## PRE-CHECK (OBRIGATORIO)
Antes de qualquer geracao, verificar se a presentations skill (@oai/artifact-tool)
esta disponivel via:
1. Variavel de ambiente `PRESENTATIONS_SKILL_DIR`.
2. Cache do codex: `~/.codex/plugins/cache/openai-primary-runtime/presentations/`.
Se ausente: NAO simule geracao. Reporte:
  "Dependencia ausente: presentations skill (@oai/artifact-tool) nao encontrada.
   Configure PRESENTATIONS_SKILL_DIR apontando para o diretorio da skill."
E pare.

## RACIOCINIO (passos)
1. Executar pre-check da presentations skill.
2. Resolver template/versao via template-routing.
3. Carregar e normalizar input (JSON ou Markdown).
4. Validar required_fields do slide-map -> se faltar campo obrigatorio, perguntar.
5. Chamar o runner para gerar deck via Node + @oai/artifact-tool.

## LIMITACAO ATUAL (documentada)
O render embutido produz um layout canonico de KPIs e NAO aplica o
`template.pptx`/`slide-map.yaml` registrado. Tratar como gerador de KPIs
canonico ate que o render parametrizado seja implementado (ver backlog P1).

## RUBRICA / REGRAS DE DECISAO
- Skill ausente: parar e reportar.
- Campo obrigatorio faltando: perguntar antes de gerar.
- Saida default: `docs/generated/<id>-deck.pptx`.

## SAIDA
- "Deck gerado: <path>"
- "Preview: <path>.png"
- "Layout: <path>.layout.json"

## NAO FACA
- Nao simule geracao se a skill estiver ausente.
- Nao invente conteudo; gere apenas com dados reais.
