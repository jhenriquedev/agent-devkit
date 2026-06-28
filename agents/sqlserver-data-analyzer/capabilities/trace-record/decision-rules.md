# Decision Rules: Trace Record

- Rastrear registros somente por consultas read-only e predicados especificos.
- Exigir identificador, filtro ou query segura suficiente para evitar varredura ampla.
- Aplicar `TOP`, timeout de statement/conexao e `LOCK_TIMEOUT`.
- Mascarar CPF, CNPJ, email, telefone, nome, endereco, token, senha e segredos.
- Nao seguir relacionamentos recursivamente sem escopo e limite claros.
- Diferenciar registro encontrado, multiplos candidatos, nao encontrado e query inconclusiva.
- Nao alterar status, corrigir dado, marcar registro ou disparar reprocessamento.
- Registrar filtros usados e lacunas para auditoria.
- Bloquear escrita, `EXEC` livre e comandos administrativos.
- Nao imprimir connection string, usuario, senha, host completo ou URL completa.
