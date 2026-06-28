# Decision Rules

- Promover versao somente apos aprovacao explicita.
- Verificar que a versao existe e tem artefatos obrigatorios completos.
- Atualizar `current_version` apenas para versao validada ou aprovada para validacao.
- Registrar promocao no changelog com motivo e data quando possivel.
- Nao alterar arquivo `template.pptx` durante promocao.
- Nao apagar status historico de versoes anteriores.
- Se a versao tiver schema ou slide-map incompleto, bloquear promocao.
- Sem confirmacao, retornar plano de promocao sem escrita.
- Preservar paths relativos e portaveis.
- A promocao deve deixar uma unica `current_version` coerente no manifest.
