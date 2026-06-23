# Workflow: Generate Operation Report

## Passos
1. Verificar que `--operation-dir` foi fornecido e que o diretorio existe.
   Se faltar, parar e perguntar.
2. Ler operation-dry-run.json (sempre presente) e operation-result.json (opcional —
   presente apenas quando a operacao foi executada).
3. Renderizar operation-report.md via report_renderer. Esta capability e read-only:
   nao chama AWS, nao executa nenhuma mutacao.
4. Se operation-result.json ausente, o relatorio documenta uma operacao apenas planejada.
5. Nunca incluir payload bruto; apenas hashes ja presentes nos artefatos.

## Regras de decisao
- operation-dry-run.json ausente => erro: artefatos da operacao nao encontrados.
- Esta capability nunca executa ou re-executa operacoes AWS.
- Payload ou secrets identificados nos artefatos => nao os propagar no relatorio.

## Criterio de parada
Falhar se operation-dry-run.json nao existe no diretorio informado.
