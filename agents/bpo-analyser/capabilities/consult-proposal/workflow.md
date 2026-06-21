# Workflow

1. Validar numero da proposta.
2. Chamar `ServicoAPI.consultarPropostaPorNumeroProposta` diretamente na BPO.
3. Normalizar status, situacao, atividade, valores e observacoes.
4. Renderizar resumo sem expor senha, CPF completo ou SOAP bruto.
