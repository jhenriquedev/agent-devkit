# Prompt: Generate Technical Docs

## OBJETIVO
Consolidar documentação técnica Markdown canônica da integração e gerar PDF
derivado quando solicitado, reunindo contrato, fluxo, lacunas e massa de testes.

## ENTRADAS
- Mesmas flags de origem (`--url`, `--file`, `--directory`, `--text`)
- `--md-output` (opcional — salva Markdown em arquivo)
- `--pdf-output` (opcional — salva PDF derivado)
- `--output` (opcional — saída padrão)

## RACIOCÍNIO
1. Extraia contrato completo (protocolos, auth, operações, erros).
2. Inclua fluxo recomendado, informações ausentes e massa de testes.
3. Markdown é a fonte canônica; PDF deriva do MESMO conteúdo, sem divergência.
4. Separe explicitamente evidências (fatos documentados) de inferências e
   perguntas pendentes.

## RUBRICA / REGRAS DE DECISÃO
- Se reportlab não estiver disponível e `--pdf-output` for solicitado, emita
  aviso claro (não falhe silenciosamente).
- Mascarar segredos no Markdown/PDF assim como nas demais saídas.

## SAÍDA
Markdown seguindo `generate-technical-docs-output.md`:
contrato + fluxo + lacunas + massa, com seção explícita Evidências × Inferências
× Perguntas Pendentes.

## NÃO FAÇA
- Gerar PDF com conteúdo divergente do Markdown.
- Vazar segredos (tokens, senhas, chaves) em qualquer formato de saída.
