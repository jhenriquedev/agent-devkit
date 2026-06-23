# Prompt: register-template

## OBJETIVO
Registrar um arquivo .pptx/.ppt/.potx como template versionado no repositorio de
templates do agente.

## ENTRADAS
- `--template` (obrigatorio): caminho para o arquivo .pptx/.ppt/.potx.
- `--template-id` (obrigatorio): identificador unico do template (ex.: `status-report`).
- `--name` (opcional): nome legivel do template.
- `--version` (opcional, default `0.1.0`): versao semver inicial.
- `--status` (opcional, default `draft`): `draft` | `validated` | `deprecated`.
- `--templates-root` (opcional): diretorio raiz dos templates.
- `--yes-save` (opcional): pula confirmacao interativa de gravacao.

## RACIOCINIO (passos)
1. Validar extensao do arquivo (deve ser .pptx, .ppt ou .potx) e existencia no
   sistema de arquivos.
2. Se `--yes-save` estiver ausente, PERGUNTAR ao usuario antes de salvar o template.
3. Verificar se a versao ja existe no diretorio de templates — se sim, erro (nao
   sobrescrever).
4. Chamar o runner para criar `versions/<version>/` com: `template.pptx`,
   `template.yaml`, `slide-map.yaml`, `input-schema.xlsx`, `input-schema.md`,
   `usage-notes.md` e `changelog.md`.
5. `current_version` so e setado quando `status=validated`.
6. Reportar os caminhos criados e o status registrado.

## RUBRICA / REGRAS DE DECISAO
- NUNCA registrar sobre uma versao existente (erro imediato).
- Novo template SEMPRE comeca como `draft` a menos que explicitamente indicado.
- `current_version` vazio se status != `validated`.
- Confirmacao de gravacao e obrigatoria a menos que `--yes-save` seja informado.

## SAIDA
- Linha "Template registrado: <id> <version>".
- Linha "Manifest: <path>".
- Linha "Version dir: <path>".

## NAO FACA
- Nao valide automaticamente o template (nunca mude status para `validated` sem
  pedido explicito).
- Nao popule conteudo de negocio nos schemas.
- Nao sobrescreva versao existente sob nenhuma circunstancia.
