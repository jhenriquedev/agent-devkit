# Decision Rules

- Refinar template criando nova versao; nunca sobrescrever versao validada.
- Resolver versao base antes de aplicar qualquer alteracao.
- Exigir `change_request` claro; se ambiguo, perguntar antes de gerar nova versao.
- Atualizar `slide-map.yaml`, schemas e usage notes quando placeholders ou layouts mudarem.
- Registrar todas as alteracoes no changelog.
- Manter nova versao como `draft` ate promocao ou validacao explicita.
- Preservar compatibilidade de paths e estrutura obrigatoria de template.
- Nao alterar decks ja gerados como parte do refinamento de template.
- Se a mudanca quebrar schema anterior, marcar impacto de compatibilidade.
- Nao promover automaticamente a versao refinada.
