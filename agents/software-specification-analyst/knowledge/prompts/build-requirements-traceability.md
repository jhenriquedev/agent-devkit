# Prompt: Build Requirements Traceability

## OBJETIVO
Construir matriz de rastreabilidade ligando requisitos funcionais e não
funcionais a user stories, critérios de aceite, componentes técnicos, testes,
riscos e perguntas abertas.

## ENTRADAS
- `input`: spec completa, functional-spec, user-stories, technical-spec ou
  combinação desses artefatos. Obrigatório.

## PASSOS DE RACIOCÍNIO
1. Liste todos os requisitos (RF-NNN, RNF-NNN) identificados.
2. Para cada requisito, mapeie:
   - User story(ies) que o implementam (US-NNN).
   - Critérios de aceite (CA-NNN) que o verificam.
   - Componente(s) técnico(s) responsáveis.
   - Tipo de teste que cobre (unitário/integração/E2E/regressão).
   - Risco associado (se houver).
   - Status: `Coberto` | `Parcial` | `Descoberto`.
3. Identifique requisitos sem história (gap de rastreabilidade).
4. Identifique histórias sem requisito mapeado (rastreabilidade reversa).
5. Em `strict`: exija cobertura de teste para cada CA.

## FORMATO DE SAÍDA
- **requirements-traceability.md**: tabela principal `Requisito | História |
  CA | Componente | Teste | Risco | Status`, seguida de seção de gaps
  (requisitos sem história, histórias sem requisito, CAs sem teste em strict).

## NÃO FAÇA
- Não marque `Coberto` sem evidência de história e CA mapeados.
- Não omita requisitos não funcionais da matriz.
- Não invente componente técnico não citado no input.
