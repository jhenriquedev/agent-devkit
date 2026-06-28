# Decision Rules: Explore Database Domain

- Explorar dominio por databases, schemas, tabelas, colunas e relacionamentos read-only.
- Agrupar objetos por prefixo, schema, nomes de negocio e relacionamentos conhecidos.
- Nao consultar dados brutos salvo amostras estritamente limitadas e mascaradas.
- Destacar dominios provaveis com confianca e sinais usados.
- Identificar tabelas sensiveis sem revelar valores pessoais.
- Nao criar diagrama ou relatorio final quando o objetivo for apenas exploracao.
- Registrar lacunas de permissao, catalogo incompleto ou baixa confianca.
- Aplicar `TOP`, timeout e `LOCK_TIMEOUT` em qualquer consulta.
- A saida deve orientar ERD, joins e analises futuras.
- Bloquear escrita, `EXEC` livre e comandos administrativos.
