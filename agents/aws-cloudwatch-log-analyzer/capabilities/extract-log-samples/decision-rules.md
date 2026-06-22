# Decision Rules: Extract Log Samples

- Respeitar `sample_size` e nunca transformar a amostra em dump integral.
- Suportar estrategias `first`, `error-first` e `spread`.
- Priorizar eventos de erro apenas quando a estrategia solicitar ou a investigacao pedir erro.
- Resumir mensagens longas e mascarar dados sensiveis quando necessario.
- Explicar criterio de selecao para que a amostra seja revisavel.
- Nao inferir causa raiz apenas a partir das amostras.
