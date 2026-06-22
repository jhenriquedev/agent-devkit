# Load Support Context

## Objetivo

Montar o contexto N2 sem repetir a triagem N1.

## Entradas

- `--project` e `--card` para carregar card Azure.
- `--n1-contract` ou contrato N1 em fixture.
- `--fixture` com card, comentarios e supportContext local.
- `--format` e `--output` para controlar o artefato.

## Raciocinio

1. Carregue o contrato N1 quando existir.
2. Carregue o card Azure ou o card de fixture.
3. Extraia CPF mascarado, proposta, contrato e correlation id.
4. Infira o sintoma a partir de supportContext, titulo e descricao.
5. Reuna evidencias vindas do N1 e do contexto N2.
6. Valide o handoff, incluindo `diagnosticGaps`.

## Rubrica/Regras

- Card ou contrato N1 sustenta a investigacao.
- Diagnostic gaps abertos devem acompanhar o contexto.
- CPF e e-mail nunca aparecem crus.

## Saida

JSON com `azureCardLoaded`, `n1ContractLoaded`, `card`, `entities`, `symptom`,
`evidence`, `handoff` e `fixtureSupportContext`.

## Nao faca

- Nao classifique causa raiz aqui.
- Nao acione especialistas.
- Nao reexecute o roteiro N1.
