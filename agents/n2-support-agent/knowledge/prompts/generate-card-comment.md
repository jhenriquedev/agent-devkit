# Generate Card Comment

## Objetivo

Gerar comentario tecnico curto para o card Azure.

## Entradas

- Causa raiz.
- Patch plan.
- Destino do artefato.

## Raciocinio

1. Cite categoria e confianca.
2. Cite destino ou modo de entrega do patch plan.
3. Resuma a conclusao em uma frase.
4. Preserve PII mascarada.
5. Mantenha comentario curto para card.

## Rubrica/Regras

- Comentario deve ser util para N2/dev.
- Nao deve colar o patch plan inteiro.
- Se readiness estiver bloqueado, sinalize que ha perguntas abertas.

## Saida

Markdown curto, normalmente uma linha com categoria, confianca, patch plan e
resumo.

## Nao faca

- Nao expor CPF ou e-mail cru.
- Nao incluir segredos.
