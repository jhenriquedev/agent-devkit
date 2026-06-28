# Regras

- Validar `date_column`, `metric_column` e granularidade antes da agregacao.
- Agregar por dia, semana ou mes conforme solicitado ou default documentado.
- Declarar periodos ausentes, datas invalidas e nulos da metrica.
- Tratar tendencia como resumo baseline, nao previsao garantida.
- Nao imputar periodos ausentes sem declarar a regra.
- Mascarar dados pessoais em qualquer amostra temporal.
