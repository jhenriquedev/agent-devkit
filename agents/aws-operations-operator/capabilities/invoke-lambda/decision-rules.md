# Decision Rules: Invoke Lambda

## Objetivo de decisao

Invocar uma Lambda de forma controlada, com payload redigido em artefatos e
execucao real somente com confirmacao forte.

## Entradas minimas

- `--function-name` e `--environment` sao obrigatorios.
- `resource_id` deve ser exatamente o function name.
- Execucao real exige `--execute`, `--confirm-resource <function-name>` e conta
  allowlisted.

## Quando executar

Execute em dry-run quando:

- o operador quer revisar invocacao e payload sem efeitos colaterais;
- a funcao alvo esta explicita;
- o payload pode ser representado por hash e tamanho.

Execute de fato apenas quando:

- o handler e seus efeitos colaterais sao entendidos;
- `confirm-resource` bate com o nome da funcao;
- preflight `get-function-configuration` passou;
- a conta foi validada para o ambiente.

Nao execute quando:

- o payload contem segredo que nao pode sequer ser passado ao runner;
- o usuario espera ver payload bruto em relatorio;
- `FunctionError` aparecer no post-check.

## Regras de decisao

1. Nunca imprimir payload de entrada ou saida; usar apenas marcador
   `<redacted sha256=... bytes=...>`.
2. Saida da Lambda deve ser resumida por hash e tamanho.
3. `FunctionError` torna a operacao falha mesmo com StatusCode 200.
4. Em `prd`, alertar que o handler pode executar efeitos irreversiveis.
5. Nao registrar stdout bruto quando ele puder conter payload sensivel.

## Criterios de qualidade

- Dry-run nao contem o payload bruto.
- Execucao real gera `preflight.json`, `post-check.json` e
  `operation-result.json`.
- `post-check.json` registra `status_code`, `function_error`,
  `executed_version` e `response_payload_hash`.

## Escalacao

Pedir revisao humana quando a Lambda altera dados, dispara integracoes externas,
processa clientes reais ou exige payload com PII/segredo.
