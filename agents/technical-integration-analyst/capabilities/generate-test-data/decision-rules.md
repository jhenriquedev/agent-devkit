# Decision Rules: Generate Test Data

- Dados devem usar placeholders seguros.
- Incluir cenarios negativos para auth, validacao e recurso inexistente.
- Nao gerar dados pessoais reais.
- Gerar massa valida, invalida, limite e dependente de fluxo a partir do contrato.
- Separar dados sintéticos de exemplos documentados.
- Usar IDs dinamicos como variaveis, nunca valores reais sensiveis.
- Nao inventar enum, formato ou regra de validacao ausente; marcar pergunta.
- Incluir dados para auth expirada/ausente, payload invalido, recurso inexistente e conflito quando aplicavel.
- Para mutations, incluir massa de sandbox e orientacao de cleanup.
- Mascarar ou omitir secrets em todos os exemplos.
- Quando payload tiver dados pessoais, usar placeholders claramente artificiais.
