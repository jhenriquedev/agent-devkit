# run-data-pipeline

## Objetivo
Produzir pacote reproduzivel de analise (manifest + profile + exploratory +
relatorio markdown) com cache_key para rastreabilidade e reuso.

## Entradas
- `--source` (obrigatorio).
- `--output` (obrigatorio): diretorio onde os artifacts serao gravados.
- `--sheet`, `--json-path`: seletores de sub-estrutura.
- `--max-rows`, `--max-file-mb`: controles de leitura.

## Raciocinio
1. Garanta sha256, row_count, truncated e warnings antes de continuar.
2. Execute etapas: ingestao -> profile -> exploratory -> relatorio.
3. Produza manifest.json com: status, steps (cada etapa e seu status), cache_key,
   created_at e caminhos dos artifacts.
4. Verifique que todos os paths de artifact apontam para arquivos criados.
5. Cite cache_key no resumo para reproducibilidade.

## Rubrica de decisao
- pipeline.status != "success" ou "warning" -> pipeline incompleto; nao entregue.
- cache_key ausente -> manifest invalido para reproducibilidade.
- profile.dataset.truncated=true -> declare "analise de amostra" no relatorio.
- Artifact path invalido -> sinalize como falha de etapa.

## Saida
Tabela de artifacts (tipo, caminho, tamanho), cache_key, status do pipeline,
warnings de qualidade, bloco de rastreabilidade. Aponte proximo passo sugerido.

## Nao fazer
- Nao gerar pipeline sem --output.
- Nao reportar pipeline como "completo" sem manifest.json e cache_key.
- Nao ocultar warnings de qualidade no relatorio.
