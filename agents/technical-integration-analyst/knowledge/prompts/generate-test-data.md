# Prompt: Generate Test Data

## OBJETIVO
Gerar massa de teste por operação, cobrindo casos válidos, inválidos, limites e
dependentes de fluxo, usando placeholders seguros.

## ENTRADAS
- Mesmas flags de origem (`--url`, `--file`, `--directory`, `--text`)
- `--json-output` (opcional — salva JSON da massa)
- `--output` (opcional — salva Markdown)

## RACIOCÍNIO
Para cada operação no contrato, produza quatro categorias de casos:
- **válido**: a partir de `body_example` quando disponível, ou placeholders seguros.
- **inválido**: campo obrigatório ausente ou tipo errado.
- **limite**: texto máximo (255 chars), valor zero, campo vazio.
- **dependente de fluxo**: IDs criados em operações anteriores (ex.: {{resource_id}}
  gerado por um POST que precede o GET/DELETE).

## RUBRICA / REGRAS DE DECISÃO
- Use placeholders seguros ({{resource_id}}, {{token}}, {{name}}) — nunca dados pessoais reais.
- Inclua negativos para auth (token inválido), validação e recurso inexistente.
- Casos flow-dependent referenciam simbolicamente resultados do `flow` do contrato.

## SAÍDA
- Markdown seguindo `generate-test-data-output.md` (por operação: Válida/Inválida/Limite)
- JSON em `--json-output` com estrutura `{cases: [{operation, valid, invalid, boundary}]}`

## NÃO FAÇA
- Vazar exemplos com segredos reais (tokens, senhas, CPFs, e-mails reais).
- Gerar massa para operações sem nenhuma informação de método/path.
