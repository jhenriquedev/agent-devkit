# Prompt: create-template-version

## OBJETIVO
Criar uma nova versao de template a partir de uma versao base ou de um arquivo
atualizado, sem mexer na current_version.

## ENTRADAS
- `--template-id` (obrigatorio): identificador do template.
- `--new_version` (obrigatorio): versao a criar (semver, ex: `0.2.0`).
- `--base_version` (opcional): versao base para copiar; default = `current_version`.
- `--template` (opcional): arquivo .pptx atualizado; se ausente, copia a base.

## RACIOCINIO (passos)
1. Validar que `new_version` nao existe no diretorio de templates (erro se ja existe).
2. Determinar origem:
   - Se `--template` informado: usar esse arquivo como template.pptx da nova versao.
   - Caso contrario: copiar artefatos da `base_version`.
3. Criar `versions/<new_version>/` com: `template.pptx`, `slide-map.yaml`,
   `input-schema.xlsx/.md`, `usage-notes.md`, `changelog.md`.
4. Atualizar `template.yaml` adicionando a nova versao (status: draft).
5. NAO alterar `current_version`.
6. Registrar changelog.

## RUBRICA / REGRAS DE DECISAO
- `new_version` ja existe: erro imediato.
- Nova versao sempre comeca como `draft`.
- `current_version` nao deve ser alterada nesta capability.

## SAIDA
- Caminhos da nova versao criada.
- Status = `draft` da nova versao.
- Changelog gerado.

## NAO FACA
- Nao sobrescreva versao existente.
- Nao promova automaticamente.
- Nao altere current_version.
