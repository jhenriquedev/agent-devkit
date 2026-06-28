# Regras

- Orquestrar ingestao, analise, plano, spec, geracao, revisao e artefatos finais.
- Criar diretorio de saida somente com confirmacao por `yes_create_dir`.
- Nao sobrescrever artefatos existentes sem confirmacao por `yes_overwrite`.
- Interromper entrega se quality gates bloqueantes falharem.
- Entregar `.drawio`, spec, plano, review e perguntas abertas quando aplicavel.
- Nao depender de renderizacao externa; usar validacao local antes de declarar entrega.
