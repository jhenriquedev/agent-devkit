# Decision Rules

- Depreciar versao somente com confirmacao e motivo operacional registrado.
- Nunca deletar arquivos de uma versao depreciada.
- Atualizar status para `deprecated` no manifest e registrar changelog.
- Se a versao depreciada for `current_version`, exigir nova versao corrente validada ou deixar lacuna explicita.
- Nao depreciar todas as versoes utilizaveis sem aviso de impacto.
- Preservar artefatos associados: `template.pptx`, schemas, slide-map e notes.
- Evitar alterar historico de outras versoes.
- Registrar riscos para decks que ainda dependam da versao.
- Manter paths portaveis e referencias relativas.
- Sem confirmacao, retornar plano de deprecacao sem escrita.
