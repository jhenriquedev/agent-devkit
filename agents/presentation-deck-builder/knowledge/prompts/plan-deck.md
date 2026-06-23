# Prompt: plan-deck

## OBJETIVO
Criar plano slide a slide a partir do conteudo extraido e das restricoes do template,
identificando lacunas antes de gerar o deck.

## ENTRADAS
- `--input` (obrigatorio): conteudo extraido (JSON ou `extracted-content.md`).
- `--template-id` (opcional): template alvo.
- `--template-version` (opcional): versao do template; default = current_version.

## RACIOCINIO (passos)
1. Carregar `slide-map.yaml` (required_fields por slide).
2. Mapear conteudo -> slides, decidindo narrativa:
   - Abertura (titulo, subtitulo, data).
   - KPIs/metricas (distribuir em no maximo 4 por slide).
   - Distribuicao/estado breakdown.
   - Pontos de atencao (highlights).
   - Fechamento (proximos passos).
3. Sinalizar campos obrigatorios sem dado correspondente como LACUNA.
4. Checar risco de overflow:
   - Maximo ~4 metricas/slide.
   - Maximo ~4 highlights/slide.
   - Maximo ~6 bullets por bloco de texto.
   - Titulos < 80 caracteres.
5. Se houver lacunas ou risco de overflow: PERGUNTAR ao usuario antes de prosseguir.

## RUBRICA / REGRAS DE DECISAO
- Campo obrigatorio sem valor: sempre sinalizar como LACUNA antes de gerar.
- Overflow: alertar, sugerir divisao em mais slides.
- Sem template informado: criar plano generico e alertar que template nao foi resolvido.

## SAIDA (deck-plan.md)
Por slide:
```
## Slide <n>: <proposito>
- Campos: <lista de campos>
- Conteudo proposto: <valor ou LACUNA>
- Fonte: <referencia no documento de origem>
- Lacunas: <campos sem dado>
```

## NAO FACA
- Nao gere o .pptx aqui.
- Nao preencha lacunas com invencao.
