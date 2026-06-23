# Prompt: Write User Stories

## OBJETIVO
Converter intenção ou spec funcional em épicos → features → user stories com
critérios de aceite verificáveis e rastreáveis.

## ENTRADAS
- `input`: spec, análise ou demanda. Obrigatório.
- `story_format`: `standard` | `job_story` (default `standard`).
- `include_gherkin`: `true` | `false` (default `true` para fluxos condicionais).

## PASSOS DE RACIOCÍNIO
1. Agrupe capacidades de produto em épicos por área funcional.
2. Quebre épicos em features concretas e entregáveis.
3. Para cada feature, escreva as histórias no formato:
   `"Como <ator>, quero <capacidade>, para <benefício>."`
4. Para cada história:
   - Dê um ID sequencial: US-001, US-002...
   - Escreva critérios de aceite verificáveis e objetivos.
   - Use Gherkin (`Dado/Quando/Então`) quando houver fluxo condicional,
     exceção ou estado de erro relevante.
   - Liste dependências (outras histórias, decisões pendentes).
   - Liste perguntas abertas específicas desta história.
5. Confirme que cada ator citado existe no input — não invente ator.

## RUBRICA DE CRITÉRIO DE ACEITE
- Bom: "Dado que o usuário tem saldo ≥ valor da transferência, quando confirma
  a operação, então o sistema debita o valor e exibe comprovante."
- Ruim: "O sistema deve funcionar corretamente."
- Ruim: "O sistema deve ser rápido."

## FORMATO DE SAÍDA
Épicos (tabela), Features (tabela), Histórias (US-NNN com CA, dependências,
perguntas abertas), agrupadas por épico.

## NÃO FAÇA
- Não escreva CA não testável ("deve funcionar bem", "deve ser intuitivo").
- Não invente ator não citado na fonte.
- Não feche história sem ao menos um CA verificável.
