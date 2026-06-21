# Prompt

Consulte a base restritiva por CPF em modo read-only e registre evidencia,
status e risco.

## Regras

- Nunca exponha connection string, usuario, senha ou token.
- Nunca retorne CPF completo; use sempre mascara.
- Trate `hit` como evidencia relevante, mas nao conclua o atendimento sem os
  demais checks do roteiro N1.
- Trate falha de conexao ou schema desconhecido como `unavailable`, nao como
  `clear`.
- Quando houver muitas tabelas com CPF, priorize nomes relacionados a bloqueio,
  restricao, fraude, negativacao ou impedimento.
