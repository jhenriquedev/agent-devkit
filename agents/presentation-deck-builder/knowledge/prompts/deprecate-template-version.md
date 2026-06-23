# Prompt: deprecate-template-version

## OBJETIVO
Marcar uma versao de template como `deprecated` no manifesto SEM apagar arquivos.

## ENTRADAS
- `--template-id` (obrigatorio): identificador do template.
- `--template-version` (obrigatorio): versao a deprecar.
- `--reason` (opcional): motivo da deprecacao.
- `--templates-root` (opcional): diretorio raiz.
- `--yes-confirm` (opcional): pula confirmacao interativa.

## RACIOCINIO (passos)
1. Verificar que a versao existe no manifesto. Se nao existir, erro imediato.
2. EXIGIR confirmacao explicita do usuario (write_policy: confirm), a menos que
   `--yes-confirm` seja informado.
3. Se for a `current_version`: ALERTAR o usuario antes de prosseguir e pedir que
   indique uma nova `current_version`.
4. Setar `status: deprecated` no `template.yaml` para essa versao.
5. Registrar changelog com motivo (ou "sem motivo informado").
6. Reportar: versao depreciada + aviso se era current.

## RUBRICA / REGRAS DE DECISAO
- Versao inexistente: erro imediato.
- Confirmacao obrigatoria sem `--yes-confirm`.
- Deprecar current_version: alertar, nao bloquear, mas exigir nova current.
- Arquivos fisicos nao sao deletados.

## SAIDA
- Manifest atualizado com `status: deprecated`.
- Aviso se era a `current_version`.
- Changelog atualizado com motivo.

## NAO FACA
- Nao delete arquivos do template.
- Nao deprecie silenciosamente a current_version sem alertar.
