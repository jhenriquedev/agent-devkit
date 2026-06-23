# Prompt: Analyze Multiple Projects

## OBJETIVO
Analisar dois ou mais projetos locais, mapeando fronteiras, contratos de
integração, ownership, regras duplicadas e impactos cruzados, antes de
qualquer especificação final.

## ENTRADAS
- `projects`: lista de caminhos de projetos. Obrigatório (mínimo 2).
- `depth`: `light` | `medium` | `deep` (default `medium`).
- `focus`: área de foco opcional.

## PASSOS DE RACIOCÍNIO
1. Para cada projeto, execute o mesmo raciocínio de `analyze-project-context`:
   estrutura, rotas, models, integrações, auth, testes.
2. Compare os projetos:
   - Fronteiras de responsabilidade: qual projeto é dono de qual entidade/fluxo?
   - Contratos de integração: APIs, eventos, filas, banco compartilhado.
   - Regras de negócio duplicadas ou inconsistentes entre projetos.
   - Dependências circulares ou acoplamento excessivo.
   - Gaps: quem cuida de autenticação, autorização, observabilidade?
3. Rotule cada achado: `FATO OBSERVADO` | `INFERÊNCIA` | `RISCO` |
   `PERGUNTA` | `DECISÃO PENDENTE`.
4. Identifique riscos de integração e impactos cruzados da demanda.

## RUBRICA DE PROFUNDIDADE
- `light`: mapa de fronteiras e contratos de integração observáveis.
- `medium`: adiciona duplicações, gaps e impactos cruzados por módulo.
- `deep`: análise completa incluindo versionamento de contratos, migração
  de dados, estratégia de rollout coordenado.

## FORMATO DE SAÍDA
- **multi-project-analysis.md**: tabela de projetos × responsabilidades,
  mapa de integrações (Mermaid), regras duplicadas/inconsistentes, riscos
  de integração, decisões de ownership pendentes, próximos passos.

## NÃO FAÇA
- Não misture fatos de projetos diferentes sem identificar a origem.
- Não assuma que um projeto conhece regras do outro sem evidência.
- Não produza spec final — apenas análise multi-projeto.
