# Prompt: Analyze Project Context

## OBJETIVO
Produzir documentos intermediários de análise de um projeto local ANTES de
qualquer especificação final, separando fato observado de regra de negócio
confirmada.

## ENTRADAS
- `project`: caminho do projeto local. Obrigatório.
- `depth`: `light` | `medium` | `deep` (default `medium`).
- `focus`: área de foco opcional (ex.: autenticação, pagamentos).
- O runner entrega inventário de arquivos interessantes — use-o como ponto de
  partida; não releia arquivos gerados (`node_modules`, `vendor`, `dist`,
  `build`, `target`, `.next`, `__pycache__`, `.git`).

## PASSOS DE RACIOCÍNIO
1. A partir do inventário, leia READMEs/docs, estrutura de pastas, rotas/
   endpoints/controllers, telas/componentes, services/use cases/jobs,
   models/schemas/migrations, integrações, auth/permissões, env, testes,
   observabilidade.
2. Para cada achado, rotule:
   - `FATO OBSERVADO` — evidência direta no código/docs.
   - `INFERÊNCIA` — conclusão razoável, não confirmada.
   - `REGRA CONFIRMADA` — regra validada pelo solicitante (rara nesta fase).
   - `PERGUNTA` — lacuna que precisa de validação.
   - `RISCO` — ponto de atenção técnico ou de negócio.
   - `DECISÃO PENDENTE` — escolha que precisa de dono.
3. Identifique módulos críticos: autenticação, pagamentos, dados sensíveis,
   integrações externas, pontos de falha.
4. Mapeie fluxos existentes observáveis no código.
5. Derive perguntas de negócio para regras implícitas
   (`ask_questions_when_business_rule_is_implicit: true`).

## RUBRICA DE PROFUNDIDADE
- `light`: estrutura de pastas, README, rotas principais, pontos críticos
  óbvios. Rápido — máximo 30 min de análise.
- `medium`: adiciona models, services, auth, env, testes existentes e mapa de
  integrações. Padrão para features novas em sistema existente.
- `deep`: análise completa incluindo histórico de migrations, configuração de
  observabilidade, edge cases e análise de segurança. Para mudanças grandes ou
  múltiplos projetos.

## FORMATO DE SAÍDA (10 documentos)
1. **analysis-context.md** — resumo, profundidade, inventário de arquivos, tech
   stack, estado geral do projeto.
2. **project-architecture-notes.md** — estrutura, padrões, componentes críticos,
   fronteiras de serviço.
3. **business-rules-discovered.md** — regras identificadas no código, rotuladas
   como FATO OBSERVADO ou INFERÊNCIA.
4. **critical-points.md** — riscos, débitos técnicos, pontos de falha, itens que
   bloqueiam a demanda.
5. **business-questions.md** — perguntas derivadas de lacunas, agrupadas por
   eixo (negócio, dados, segurança, integração).
6. **technical-impact-analysis.md** — componentes/módulos impactados pela
   demanda, estimativa de esforço por área.
7. **integration-map.md** — sistemas externos, APIs, eventos, jobs, filas.
8. **data-and-permissions-analysis.md** — entidades, atributos sensíveis,
   permissões observadas, gaps de dados.
9. **open-decisions.md** — decisões pendentes com dono sugerido e impacto.
10. **analysis-review.md** — resumo executivo da análise, rubrica de suficiência
    para spec final (ver `policies.yaml`), próximos passos recomendados.

## NÃO FAÇA
- Não declare regra de negócio "confirmada" a partir só do código — marque como
  `INFERÊNCIA` e gere pergunta de validação.
- Não invente integração/modelo de dados não evidenciado nos arquivos.
- Não releia diretórios gerados listados em
  `code_analysis_policy.ignore_common_generated_directories`.
- Não produza spec final nesta etapa — apenas análise.
