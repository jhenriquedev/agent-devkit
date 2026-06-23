# Prompt: compare-template-versions

## OBJETIVO
Resumir as diferencas entre duas versoes de um template, classificando o impacto
semver, sem alterar nenhuma versao.

## ENTRADAS
- `--template-id` (obrigatorio): identificador do template.
- `--from-version` (obrigatorio): versao base de comparacao.
- `--to-version` (obrigatorio): versao alvo de comparacao.
- `--templates-root` (opcional): diretorio raiz.

## RACIOCINIO (passos)
1. Ler manifesto, `slide-map.yaml`, `input-schema.md` e `usage-notes.md` das
   duas versoes.
2. Calcular diffs por dimensao:
   - Numero e ordem dos slides.
   - `required_fields` por slide (adicionados, removidos, renomeados).
   - Schema de entrada (colunas).
   - Status (draft -> validated etc.).
   - Identidade visual (se disponivel via .pptx).
3. Classificar impacto semver resultante:
   - patch: mudancas de texto/notas sem alterar estrutura.
   - minor: novo slide, campo novo, layout adicionado.
   - major: slides removidos, campos obrigatorios removidos, incompativel.
4. Recomendar acao (migrar decks existentes? Regerar input-schema?).

## RUBRICA / REGRAS DE DECISAO
- Versao inexistente: erro imediato.
- Sem diff: reportar "Versoes identicas" com nivel `patch`.

## SAIDA (template-version-comparison.md)
Tabela: | dimensao | from_version | to_version | tipo de mudanca |
Secao "Impacto semver": nivel e justificativa.
Secao "Recomendacao": migrar / regerar input / sem acao.

## NAO FACA
- Nao altere nenhuma versao.
- Nao promova nem deprecie.
