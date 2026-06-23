# Prompt: Create Functional Spec

## OBJETIVO
Gerar especificação funcional detalhada descrevendo comportamento esperado do
produto, regras de negócio, fluxos, atores e critérios de aceite.

## ENTRADAS
- `input`: demanda, spec completa ou documentos de análise. Obrigatório.
- Fonte esperada: fatos fornecidos e/ou fatos observados da análise.

## PASSOS DE RACIOCÍNIO
1. Identifique o problema a resolver e o objetivo funcional.
2. Delimite escopo e fora de escopo com precisão.
3. Liste todos os atores com seus papéis, permissões e objetivos.
4. Para cada requisito funcional:
   - Numere (RF-001, RF-002...).
   - Descreva o comportamento esperado do sistema.
   - Cite a fonte (fato fornecido ou fato observado).
   - Liste critério de aceite verificável.
5. Separe regras de negócio dos requisitos funcionais:
   - Regra de negócio: invariante do domínio (ex.: "saldo nunca pode ser negativo").
   - Requisito funcional: comportamento do sistema (ex.: "o sistema deve bloquear
     operação quando saldo < 0").
6. Descreva fluxos principais, alternativos e exceções em prosa e/ou Mermaid.

## FORMATO DE SAÍDA
- **functional-spec.md**: contexto, problema, objetivos, escopo, fora de escopo,
  atores e personas, requisitos funcionais (tabela numerada), regras de negócio,
  fluxos (Mermaid), exceções, critérios de aceite, perguntas abertas.

## NÃO FAÇA
- Não misture regra de negócio com requisito funcional.
- Não escreva critério de aceite não verificável ("deve funcionar bem").
- Não invente ator não citado no input.
- Não promova sugestão técnica a requisito de produto.
