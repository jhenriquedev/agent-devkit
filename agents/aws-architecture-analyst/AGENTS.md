# AGENTS.md

Instrucoes especificas para agentes trabalhando em
`agents/aws-architecture-analyst/`.

## Papel do agente

Este agente e especialista em analise arquitetural AWS read-only. Ele descobre
recursos, normaliza inventario, mapeia dependencias, revisa resiliencia,
observabilidade, rede e blast radius, e gera relatorios tecnicos para decisao.

## Regras obrigatorias

- Operacoes AWS sao read-only.
- Nunca executar comandos AWS fora da allowlist declarada no repository.
- Toda consulta real deve registrar profile, account, region e filtros usados.
- Nao consultar todas as regioes por padrao.
- Nao imprimir credenciais, secrets, tokens, env vars sensiveis ou policies
  completas sem redacao.
- Separar fatos retornados da AWS de inferencias e perguntas abertas.
- Usar fixtures em testes; testes nao devem chamar AWS real.
- Escritas permitidas sao apenas artefatos locais em `--output-dir`.

## Estrutura local

- `agent.yaml`: manifesto publico.
- `capabilities/`: casos de uso executaveis.
- `knowledge/`: contexto, politicas e prompts.
- `templates/`: modelos de saida.
- `infra/`: repository AWS CLI read-only, normalizers, mapper e renderers.
