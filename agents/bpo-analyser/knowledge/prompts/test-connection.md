# Prompt: Test BPO Connection

## Objetivo

Verificar se o BPO Analyser esta configurado e, se solicitado, se os endpoints
SOAP estao acessiveis, sem expor credenciais.

## Entradas

- `--network` opcional: alem da configuracao local, consulta WSDL dos endpoints.
- `--fixture` e `--output` opcionais para execucao offline ou arquivo.

## Raciocinio

1. Confirme presenca de `BPO_SERVICO_API_URL`, `BPO_WS_PROPOSTA_URL`,
   `BPO_CARTAO_USER` e `BPO_CARTAO_PASSWORD`.
2. Sem `--network`, valide apenas configuracao local.
3. Com `--network`, leia o status WSDL de cada endpoint configurado.
4. Endpoints opcionais de esteira, formalizacao e consignacao podem estar vazios.

## Decisao

- Variavel obrigatoria ausente e bloqueio de configuracao.
- WSDL com erro e indisponibilidade de endpoint, nao falha analitica do agente.
- WSDL respondendo nao prova saude funcional completa de proposta.

## Saida

Diagnostico com configurado, usuario/senha configurados sem valores, timeout, TLS
verify e tabela de endpoints com status de rede.

## Nao faca

Nao imprima valores de usuario, senha, token ou variaveis sensiveis. Nao chame
consulta de proposta. Nao conclua saude funcional so porque WSDL respondeu.
