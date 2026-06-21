# Workflow

1. Validar CPF e normalizar para digitos.
2. Chamar `ServicoAPI.listarPropostasPorCpf` diretamente na BPO.
3. Normalizar propostas retornadas.
4. Renderizar lista com CPF mascarado.
