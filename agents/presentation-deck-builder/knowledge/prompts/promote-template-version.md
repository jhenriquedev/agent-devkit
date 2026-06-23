# Prompt: promote-template-version

## OBJETIVO
Definir uma versao como `current_version` apos aprovacao, marcando-a como
`validated` no manifesto.

## ENTRADAS
- `--template-id` (obrigatorio): identificador do template.
- `--template-version` (obrigatorio): versao a promover.
- `--templates-root` (opcional): diretorio raiz.
- `--yes-confirm` (opcional): pula confirmacao interativa.

## RACIOCINIO (passos)
1. Verificar que a versao existe no manifesto (`template.yaml`). Se nao existir,
   erro imediato com mensagem "template version not found in manifest".
2. EXIGIR confirmacao explicita do usuario antes de aplicar (write_policy: confirm),
   a menos que `--yes-confirm` seja informado.
3. Atualizar `template.yaml`: setar `current_version = <version>` e marcar a versao
   como `validated` se ainda for `draft`.
4. Registrar changelog: "Versao <version> promovida para current_version."
5. Reportar: versao anterior x nova current_version.

## RUBRICA / REGRAS DE DECISAO
- Versao inexistente no manifesto: erro imediato (nao criar).
- Confirmacao obrigatoria sem `--yes-confirm`.
- Nao deprecar a versao anterior automaticamente.

## SAIDA
- Manifest atualizado com `current_version: <version>`.
- Linha informando versao anterior e nova current.
- Changelog atualizado.

## NAO FACA
- Nao promova sem confirmacao.
- Nao deprecie a versao anterior automaticamente.
- Nao crie versao se nao existir.
