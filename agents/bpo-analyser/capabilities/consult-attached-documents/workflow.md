# Workflow

1. Validar numero da proposta e tipo de documento.
2. Chamar `WsProposta.ConsultaDocumentosAnexados` diretamente na BPO.
3. Normalizar nome, tipo, extensao, tamanho e indicadores de conteudo.
4. Omitir conteudo base64 por padrao.
