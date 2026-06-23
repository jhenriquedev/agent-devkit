# Prompt: ingest-source-document

## OBJETIVO
Extrair conteudo estruturado de um documento (PDF, Markdown, CSV, DOCX, XLSX, TXT)
sem inventar dados ausentes, produzindo `extracted-content.md`.

## ENTRADAS
- `--input` (obrigatorio): caminho do documento de origem.
- `--output` (opcional): caminho para o arquivo de saida.

## RACIOCINIO (passos)
1. Detectar formato pelo sufixo (.pdf, .md, .csv, .docx, .xlsx, .txt).
2. Extrair: titulo, subtitulo, secoes, metricas, listas e tabelas.
3. Normalizar para estrutura: `{title, subtitle, metrics[], state_breakdown{},
   highlights[], footer}` compativel com o input do gerador de deck.
4. Identificar lacunas: campos sem fonte no documento original marcados como "?".
5. Escrever `extracted-content.md` com blocos estruturados + secao de lacunas.

## RUBRICA / REGRAS DE DECISAO
- NUNCA invente numeros, nomes ou conteudo ausente no documento original.
- Campos sem fonte: marcar como "?" (nao preencher com estimativa).
- Se o formato nao for suportado: reportar e parar.

## SAIDA (extracted-content.md)
```
# Conteudo Extraido: <nome do arquivo>

## Estrutura
- title: <valor ou ?>
- subtitle: <valor ou ?>
- metrics: <lista ou vazia>
- state_breakdown: <mapa ou vazio>
- highlights: <lista ou vazia>
- footer: <valor ou ?>

## Lacunas
- <campo>: nao encontrado no documento de origem
```

## NAO FACA
- Nao invente numeros nem nomes ausentes.
- Nao altere o documento de origem.
