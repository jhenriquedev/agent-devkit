# Contexto

PyAutoGUI controla mouse, teclado e screenshots sobre a interface grafica atual.
Isso torna automacoes frageis diante de mudancas de janela, escala, resolucao,
foco, idioma, tema e layout.

Use este agente quando:

- a tarefa depende de aplicativo desktop sem API;
- nao ha CLI;
- nao ha MCP/tool oficial;
- automacao web nao se aplica;
- automacao nativa do sistema operacional nao e opcao mais segura;
- o usuario aceita explicitamente o risco visual.

Evite este agente quando a tarefa puder ser resolvida por integracao
deterministica, browser automation ou comandos nativos.
