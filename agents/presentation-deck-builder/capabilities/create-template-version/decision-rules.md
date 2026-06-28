# Decision Rules

- Criar sempre uma nova pasta `versions/<new-version>/`; nunca sobrescrever versao existente.
- Resolver a versao base explicitamente ou usar `current_version` quando apropriado.
- Se a base estiver validada, preservar o arquivo original intacto.
- Copiar ou receber novo `.pptx` mantendo manifest, schema, slide-map e usage notes coerentes.
- Atualizar `template.yaml` e `changelog.md` com motivo, origem e status inicial.
- Marcar nova versao como `draft` ate validacao ou promocao explicita.
- Regerar schemas quando placeholders ou slide-map mudarem.
- Rejeitar `new_version` igual a uma versao ja registrada.
- Manter paths portaveis em macOS, Windows e Linux.
- Nao promover automaticamente a nova versao para `current_version`.
