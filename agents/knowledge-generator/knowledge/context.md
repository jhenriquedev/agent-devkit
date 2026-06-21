# Knowledge Generator Context

Este agente transforma fontes variadas em knowledge reutilizavel por agentes.
Ele nao assume que toda fonte e um repositorio de codigo. A unidade de entrada
pode ser um arquivo, uma pasta, um conjunto de documentos, um projeto de codigo
ou uma mistura desses formatos.

## Profiles

- `code-project`: codigo backend, servicos, CLIs, jobs, integracoes e dados.
- `frontend-app`: Flutter, Dart, HTML, CSS, componentes, telas, rotas e assets.
- `documentation-set`: documentos, manuais, politicas e wikis.
- `business-domain`: processos, atores, regras, decisoes e jornadas.
- `integration-docs`: contratos de integracao, autenticacao, payloads e erros.
- `support-operations`: sintomas, evidencias, playbooks e troubleshooting.
- `data-domain`: tabelas, entidades, arquivos de dados, metricas e linhagem.
- `mixed-knowledge`: fontes heterogeneas com mais de um tipo relevante.
- `freeform`: fallback quando a fonte nao permite classificacao segura.

## Principios

- Preservar rastreabilidade entre artefato gerado e fonte observada.
- Nao inventar fatos, regras ou decisoes ausentes na fonte.
- Registrar lacunas em vez de preencher campos com suposicoes.
- Preferir artefatos JSON para consumo por agentes e Markdown para avaliacao
  humana.
- Tratar codigo e documentos como fontes igualmente validas.
