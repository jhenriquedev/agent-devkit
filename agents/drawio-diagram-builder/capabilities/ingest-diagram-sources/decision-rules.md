# Regras

- Ler fontes como read-only e preservar rastreabilidade de caminho, tipo e origem.
- Ignorar diretorios gerados comuns como `.git`, `node_modules`, `vendor`, `dist`, `build`, `target` e `.next`.
- Separar fatos extraidos, inferencias, premissas e perguntas abertas no contexto normalizado.
- Nao depender de servico externo para interpretar fontes locais.
- Resumir conteudo grande e registrar limites de leitura ou arquivos ignorados.
- Gerar artefato de contexto somente quando `output` for informado.
