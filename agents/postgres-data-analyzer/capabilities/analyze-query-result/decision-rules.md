# Decision Rules: Analyze Query Result

- Analisar somente resultados ja obtidos ou queries read-only validadas.
- Nao executar escrita, DDL, procedures, `COPY`, `DO` ou comandos administrativos.
- Aplicar mascaramento em CPF, CNPJ, e-mail, telefone, token, senha e campos pessoais.
- Descrever cardinalidade, nulos, tipos aparentes, outliers simples e sinais de sensibilidade.
- Nao inferir causa de negocio sem evidencias nos dados e no contexto do solicitante.
- Registrar limites da amostra e evitar generalizacao quando o resultado for pequeno.
- Manter linhas representativas reduzidas e sem dumps pessoais extensos.
- Indicar proximos checks read-only quando a analise for inconclusiva.
