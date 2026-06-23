# Prompt: review-generated-deck

## OBJETIVO
Revisar um deck gerado quanto a aderencia ao template e qualidade, produzindo
`deck-review.md` com veredito (aprovado / refinar).

## ENTRADAS
- `--deck` (obrigatorio): caminho do arquivo .pptx gerado.
- `--template-id` (opcional): template de referencia.
- `--template-version` (opcional): versao do template.

## RACIOCINIO (passos)
1. Carregar (quando possivel) o deck e o template de referencia.
2. Verificar cada item do checklist de qualidade:
   a. Identidade visual preservada (fontes, cores, layout compativel).
   b. Nenhum placeholder vazio (titulo, subtitulo, metricas).
   c. Campos obrigatorios do slide-map presentes.
   d. Sem overflow: maximo ~4 metricas, ~4 highlights, ~6 bullets, titulos < 80 chars.
   e. Slides nao superlotados.
   f. Titulos coerentes com o proposito de cada slide.
3. Para cada item: status (ok / alerta / falha), evidencia, acao sugerida.
4. Veredito final: aprovado (todos ok/alerta) ou refinar (alguma falha).

## RUBRICA / REGRAS DE DECISAO
- `falha`: campo obrigatorio ausente, placeholder vazio, overflow severo.
- `alerta`: identidade levemente divergente, texto longo.
- `ok`: tudo conforme.

## SAIDA (deck-review.md)
```
# Deck Review: <nome do deck>

| item | status | evidencia | acao sugerida |
|---|---|---|---|
| identidade visual | ok/alerta/falha | ... | ... |
| ...

## Veredito: Aprovado / Refinar
```

## NAO FACA
- Nao edite o deck; e read-only.
- Nao gere novo deck aqui; encaminhe para refine-generated-deck.
