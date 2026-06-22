# Decision Rules: Analyze Service Error

- Filtrar eventos que indiquem error, exception, fail, fatal ou warning.
- Agrupar mensagens normalizadas para reduzir ids e numeros variaveis.
- Listar status codes e endpoints quando forem encontrados nos eventos.
- Hipoteses devem ser condicionais e baseadas nos padroes observados.
- Nao afirmar causa raiz sem evidencia convergente de logs, deploy ou dependencia externa.
- Resumir stack traces, payloads e campos potencialmente sensiveis.
