# Prompt: Analyze Integration Flow

## OBJETIVO
Inferir a ordem recomendada de uso da integração, considerando pré-condições,
dependências entre operações, risco de mutations e necessidade de cleanup.

## ENTRADAS
- Mesmas flags de origem (`--url`, `--file`, `--directory`, `--text`)
- `--output` (opcional)

## RACIOCÍNIO
1. Coloque auth/obtenção de token antes de chamadas protegidas.
2. Ordene: setup/criação (POST) → consultas (GET) → atualização (PUT/PATCH)
   → destrutivas (DELETE) → validação → cleanup.
3. Aponte pré-condições, IDs dinâmicos encadeados (ex.: {{resource_id}}) e
   rollback quando aplicável.

## RUBRICA / REGRAS DE DECISÃO
- Operações destrutivas SEMPRE ficam no fim e exigem nota de ambiente seguro.
- Se auth estiver ausente no contrato, o primeiro passo deve mencionar a lacuna.
- Se não há operações, emita passo único pedindo para completar informações.

## SAÍDA
Markdown seguindo `analyze-integration-flow-output.md`:
lista numerada "Ordem recomendada" com sufixo "(mutation)" para operações
que modificam estado.

## NÃO FAÇA
- Sugerir execução destrutiva sem ressalva de ambiente seguro.
- Inventar IDs ou valores concretos — use placeholders simbólicos.
