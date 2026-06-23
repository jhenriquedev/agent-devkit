# Prompt: refine-template

## OBJETIVO
Aplicar um change_request a um template existente criando NOVA versao,
preservando a base validada intacta.

## ENTRADAS
- `--template-id` (obrigatorio): identificador do template.
- `--change_request` (obrigatorio): descricao das mudancas desejadas.
- `--base_version` (opcional): versao base; default = `current_version`.
- `--new_version` (opcional): versao a criar; se ausente, calcular via semver.

## RACIOCINIO (passos)
1. Resolver `base_version` (default = `current_version`).
2. Se `base_version` tiver `status: validated`, PROIBIDO sobrescrever -> criar
   nova versao obrigatoriamente.
3. Calcular bump semver:
   - patch: mudancas de texto, notas, placeholders sem alterar estrutura.
   - minor: novo slide, novo layout, mudanca de schema de entrada.
   - major: incompativel com versao anterior (reorganizacao total).
4. Chamar runner para: copiar `base_version`, aplicar mudancas, criar
   `versions/<new_version>/` com todos os artefatos.
5. Registrar changelog com descricao do change_request e bump aplicado.
6. NAO promover a nova versao automaticamente.

## RUBRICA / REGRAS DE DECISAO
- Base `validated`: nova versao e obrigatoria, nunca sobrescrever.
- Base `draft`: ainda assim criar nova versao (preservar historico).
- Bump semver deve ser justificado na resposta.

## SAIDA
- Caminhos da nova versao criada.
- Changelog gerado.
- Bump aplicado e justificativa.

## NAO FACA
- Nao altere a versao base validada.
- Nao promova a nova versao automaticamente.
- Nao invente conteudo de negocio nos schemas.
