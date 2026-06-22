# Decision Rules: Detect Error Patterns

- Usar eventos de erro quando existirem; caso contrario, deixar claro que a amostra nao contem erro detectado.
- Suportar agrupamento por mensagem, status code, endpoint ou stream.
- Mostrar frequencia antes de exemplos e limitar amostras por padrao.
- Nao inferir causa raiz por frequencia isolada.
- Normalizar mensagens para ids e numeros variaveis sem unir erros semanticamente distintos.
- Tratar baixa contagem ou janela estreita como lacuna de analise.
