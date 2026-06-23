# Prompt: Conduct Requirements Interview

## OBJETIVO
Conduzir uma entrevista de requisitos em pt-BR e produzir três artefatos:
`interview-guide.md`, `stakeholder-questions.md` e `missing-decisions.md`,
adaptando volume e profundidade ao escopo da demanda.

## ENTRADAS
- `input`: demanda inicial (Markdown/texto). Obrigatório.
- `analysis_dir`: pasta com documentos de análise já produzidos (opcional). Se
  presente, herde as perguntas em aberto desses documentos.
- `depth`: `light` | `medium` | `deep` (default `medium`).
- `audience`: público da entrevista (opcional).

## PASSOS DE RACIOCÍNIO
1. Leia a demanda e (se houver) os `.md` de `analysis_dir`.
2. Classifique/confirme a profundidade; em `light`, faça poucas perguntas
   focadas; em `deep`, cubra todos os grupos e exceções.
3. Extraia conceitos/termos a validar e perguntas já abertas na análise.
4. Agrupe as perguntas por: negócio, funcional, técnico, dados, segurança, QA
   (conforme `interview_policy.group_questions_by` em `policies.yaml`).
5. Marque quais decisões estão bloqueadas e quem é o dono sugerido.

## ROTEIRO DE ENTREVISTA
Use como base e corte o que não couber na profundidade escolhida.

### A. Abertura
- Qual problema de negócio esta demanda resolve? Para quem?
- Como saberemos que deu certo? Qual métrica/resultado mensurável?
- Há prazo, restrição regulatória ou dependência externa conhecida?

### B. Negócio e regras
- Quais regras atuais são obrigatórias e quais podem mudar?
- Existem exceções, casos especiais ou tratamentos manuais hoje?
- O que NÃO faz parte deste escopo?

### C. Atores e permissões
- Quem executa a jornada principal? Quais outros papéis participam?
- Quem pode criar, alterar, consultar, aprovar e concluir?
- Há segregação de funções, auditoria ou aprovação obrigatória?

### D. Funcional e fluxos
- Qual é o caminho feliz, passo a passo?
- Quais fluxos alternativos e exceções precisam existir?
- Quais estados/transições o item percorre? Quais mensagens o usuário vê?

### E. Dados
- Quais dados são obrigatórios, opcionais, sensíveis ou auditáveis?
- Qual a origem de cada dado? Há retenção/anonimização exigida?

### F. Integrações e técnico
- Há sistemas externos, eventos, jobs ou filas envolvidos?
- Há restrição de stack, performance, disponibilidade ou rollback?

### G. QA e aceite
- Quais cenários são críticos para regressão?
- Quais dados de teste representam casos reais?
- Qual o critério mínimo para considerar a entrega aceita?

## RUBRICA DE VOLUME
- `light`: blocos A, B (essencial), G. ~6–10 perguntas.
- `medium`: A–G, sem exaustividade em F. ~12–20 perguntas.
- `deep`: A–G completos + exceções e edge cases. Sem teto, mas sem repetição.

## FORMATO DE SAÍDA
- **interview-guide.md**: profundidade, objetivo, contexto citado, conceitos a
  validar, sequência recomendada.
- **stakeholder-questions.md**: perguntas agrupadas pelos 6 eixos (negócio,
  funcional, técnico, dados, segurança, QA) + perguntas herdadas da análise.
- **missing-decisions.md**: tabela `Decisão | Por que importa | Dono sugerido`.

## NÃO FAÇA
- Não faça questionário longo quando o escopo é pequeno.
- Não responda as próprias perguntas com suposição.
- Não transforme dúvida em requisito.
- Não omita perguntas bloqueantes por parecerem óbvias.
