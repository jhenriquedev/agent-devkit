# Prompt: Analyze Service Errors

## Objetivo
Analisar erros de um serviço numa janela e agrupá-los por nível, tipo e padrão de
mensagem, separando evidência de inferência.

## Entradas esperadas
- Obrigatórias: `--source`, `--from`, `--to`.
- Recomendadas: `--service`, `--environment`. Opcional `--level` (default "error"), `--query`.

## Raciocínio
1. Se `--service`/`--environment` faltarem, sinalize que a análise é ampla e sugira filtrar.
2. Colete eventos de nível erro no escopo.
3. Agrupe por padrão de mensagem (fingerprint) e, quando possível, por error.type / level.
4. Apresente os padrões mais frequentes + amostras limitadas (<=10) + próximos passos.

## Regras de decisão
- Agrupamento por fingerprint é INFERÊNCIA heurística, rotule como tal. Ver também: decision-rules.md.
- Mantenha amostras cruas limitadas.
- Destaque explicitamente se faltou filtro de service ou environment.

## Formato de saída
Cabeçalho de escopo + "Error Patterns" (contagem) + "Samples" + "Inferences".

## Não fazer
- Não afirmar causa-raiz; padrão != causa.
- Não confundir contagem de amostra carregada com total real de erros (use count quando dúvida).
