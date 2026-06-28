# Decision Rules: Trace Record

- Rastrear registros somente por consultas read-only e predicados especificos.
- Exigir identificador, filtro ou query segura suficiente para evitar varredura ampla.
- Aplicar limite automatico e `statement_timeout`.
- Mascarar CPF, CNPJ, e-mail, telefone, token, senha e campos pessoais.
- Nao seguir relacionamentos recursivamente sem escopo e limite claros.
- Diferenciar registro encontrado, multiplos candidatos, nao encontrado e query inconclusiva.
- Nao alterar status, marcar registro, corrigir dado ou disparar reprocessamento.
- Registrar filtros usados e lacunas para auditoria.
