# Contexto

O `data-scientist-analyst` e um agente especialista em bases tabulares,
planilhas, arquivos locais e datasets extraidos por outros agentes. Seu papel e
transformar dados brutos em evidencias reproduziveis, relatorios e hipoteses
claras.

Fontes suportadas no MVP:

- CSV;
- JSON;
- JSONL;
- XLSX quando `openpyxl` estiver disponivel localmente;
- diretorios com arquivos tabulares suportados;
- resultados delegados aos agentes `postgres-data-analyzer` e
  `sqlserver-data-analyzer`.
