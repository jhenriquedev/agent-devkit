# Prompt: Map User Journeys

## OBJETIVO
Mapear jornadas de usuário, fluxos alternativos e exceções em Markdown com
diagramas Mermaid, cobrindo caminhos felizes, caminhos alternativos e estados
de erro.

## ENTRADAS
- `input`: spec funcional, análise ou demanda. Obrigatório.
- `actors`: lista de atores a cobrir (opcional; se ausente, derivar do input).

## PASSOS DE RACIOCÍNIO
1. Identifique todos os atores e suas jornadas principais.
2. Para cada jornada:
   - Mapeie o caminho feliz (happy path) passo a passo.
   - Identifique pontos de decisão e ramificações.
   - Mapeie fluxos alternativos (usuário corrige dados, aprova, rejeita).
   - Mapeie exceções (sem permissão, dado inválido, falha de integração).
   - Identifique handoffs: onde o sistema aguarda ação externa ou humana.
3. Produza diagrama Mermaid `flowchart TD` para a jornada principal e para
   cada fluxo alternativo relevante.
4. Liste os estados do objeto principal ao longo da jornada.
5. Aponte perguntas abertas sobre fluxos não confirmados.

## FORMATO DE SAÍDA
- **journey-flows.md**: lista de jornadas por ator, jornada principal com
  diagrama Mermaid, fluxos alternativos com diagramas, exceções documentadas,
  mapa de estados do objeto, perguntas abertas sobre fluxos.

## NÃO FAÇA
- Não invente fluxo não evidenciado no input.
- Não omita exceções comuns (sem permissão, falha de integração, dado inválido).
- Não use Mermaid com sintaxe inválida — valide a estrutura do diagrama.
- Não misture jornadas de atores diferentes no mesmo diagrama sem legenda.
