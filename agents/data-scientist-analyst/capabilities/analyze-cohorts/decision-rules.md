# Regras

- Validar coluna de cohort e coluna de evento como datas antes de calcular idade.
- Calcular idade em dias desde a entrada e nao permitir idade negativa sem sinalizar anomalia.
- Reportar contagem por cohort antes de metricas opcionais.
- Nao comparar cohorts com baixa contagem como se fossem equivalentes.
- Mascarar identificadores em exemplos de eventos.
- Declarar janelas incompletas e censura temporal como limitacao.
