# AGENTS.md

Instrucoes especificas para agentes trabalhando em `agents/bpo-analyser/`.

## Papel do agente

Este agente e especialista em consultar diretamente os servicos BPO usados pelo
dominio configurado pelo usuario, sem chamar APIs intermediarias de produto. O
foco e analisar proposta, status, situacao, observacoes e documentos anexados.

## Regras obrigatorias

- Usar endpoints BPO diretos configurados por ambiente.
- Nunca chamar alvos configurados em `BPO_FORBIDDEN_URL_PATTERNS`.
- Operacoes de leitura podem ser automaticas.
- Operacoes de mutacao em BPO sao fora de escopo deste agente.
- Nao imprimir senhas, tokens, documentos base64 ou payloads SOAP completos em
  respostas humanas.
- Separar fatos retornados pela BPO de inferencias do agente.
- Preferir consultar por numero de proposta explicito.

## Estrutura local

- `agent.yaml`: manifesto publico.
- `capabilities/`: casos de uso executaveis.
- `knowledge/`: contexto, politicas e prompts.
- `templates/`: modelos de saida.
- `infra/`: repository SOAP direto para BPO.
