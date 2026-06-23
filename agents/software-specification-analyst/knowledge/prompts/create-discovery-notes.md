# Prompt: Create Discovery Notes

## OBJETIVO
Criar notas de descoberta iniciais a partir de uma demanda ou conversa,
classificando a profundidade necessária e recomendando os próximos artefatos.

## ENTRADAS
- `input`: demanda, card, ata ou texto inicial. Obrigatório.
- `depth`: `light` | `medium` | `deep` (opcional; se não fornecido, classificar).

## PASSOS DE RACIOCÍNIO
1. Leia o input e identifique o tipo de solicitação: nova feature, melhoria,
   correção, integração, refatoração, múltiplos projetos.
2. Classifique a profundidade necessária com a rubrica:
   - `light`: demanda pequena/bem descrita, sem sistema existente.
   - `medium`: feature nova em sistema existente, regras implícitas presentes.
   - `deep`: mudança grande, múltiplos projetos, integrações, regras críticas.
3. Separe e rotule cada informação:
   - `FATO FORNECIDO` — dado explícito no input.
   - `INFERÊNCIA` — interpretação razoável.
   - `PREMISSA` — assumida para continuar.
   - `LACUNA` — informação que falta e bloqueia ou levanta risco.
4. Liste hipóteses de trabalho a validar.
5. Defina os próximos artefatos recomendados com base na profundidade.

## FORMATO DE SAÍDA
- **discovery-notes.md**: profundidade classificada (com justificativa),
  fatos fornecidos, inferências, premissas, lacunas identificadas, hipóteses
  de trabalho, próximos artefatos recomendados e perguntas imediatas.

## NÃO FAÇA
- Não misture lacuna com fato fornecido.
- Não classifique como `deep` o que é claramente `light`.
- Não gere spec ou user stories nesta etapa — apenas descoberta inicial.
