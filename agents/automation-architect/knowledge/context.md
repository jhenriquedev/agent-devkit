# Contexto

O Agent DevKit possui builders especializados para automacoes Python, Selenium,
PyAutoGUI, Lambda, Docker e loops de execucao. Este agente fica acima deles e
decide qual caminho usar.

Heuristica principal:

1. Preferir API, CLI ou repository quando disponivel.
2. Usar Python deterministico para automacoes locais, arquivos, APIs simples e
   tarefas repetitivas.
3. Usar Selenium apenas quando houver requisito explicito de WebDriver, Selenium
   Grid ou legado.
4. Usar PyAutoGUI apenas como ultimo recurso para aplicacao desktop sem API.
5. Usar Lambda quando a automacao for event-driven, cloud/serverless ou precisar
   execucao gerenciada.
6. Usar Docker quando o problema central for empacotamento, isolamento ou
   reprodutibilidade.
7. Usar loop engineering quando houver repeticao controlada, retry, budget,
   criterio de parada ou agendamento local.
8. Playwright e uma recomendacao valida para web sem API, mas ainda nao possui
   builder versionado neste item.
