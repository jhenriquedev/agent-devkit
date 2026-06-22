# Prompt: Generate Incident Report

## Objetivo

Gerar relatorio operacional de incidente a partir de eventos CloudWatch com
timeline, evidencias, hipoteses e proximos passos.

## Entradas

- `service` e `environment`: contexto do incidente.
- `region`, `log_group`, `start_time`, `end_time`: escopo CloudWatch.
- `incident_id`: identificador externo opcional.
- `filter_pattern`, `log_stream_prefix` e `limit`: refinamento opcional.

## Regras

- Separar sumario executivo, timeline, evidencias, hipoteses e lacunas.
- Nao afirmar impacto de negocio sem dado externo.
- Nao afirmar causa raiz definitiva sem convergencia de evidencias.
- Destacar eventos de erro e contagens.
- Manter o relatorio pronto para revisao humana.

## Saida

- Renderize sumario com servico, ambiente, janela e totais.
- Liste timeline com eventos representativos.
- Inclua hipoteses condicionais e validacoes recomendadas.
- Informe que nenhuma escrita foi executada.

## Nao faca

- Nao atualizar incidente ou card.
- Nao ocultar lacunas relevantes.
- Nao incluir payload bruto sensivel.
