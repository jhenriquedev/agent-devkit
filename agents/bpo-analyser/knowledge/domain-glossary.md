# Glossario de Dominio BPO

Este arquivo espelha as regras canônicas implementadas em
`infra/integrations/bpo/bpo_repository.py`. Se houver divergencia, corrija o
codigo e este glossario juntos.

## Situacoes BPO

| Codigo ou texto | Classe normalizada | Uso operacional |
|---|---|---|
| `INT`, `INTEGRADA` | `integrada` | Proposta integrada. Pode ser elegivel se cumprir a politica configurada. |
| `APR`, `APROVADA` | `aprovada` | Proposta aprovada. Pode ser elegivel se cumprir a politica configurada. |
| `CAD`, `CADASTRADA` | `cadastrada` | Proposta cadastrada, em analise. |
| `PEN`, `PENDENTE` | `pendente` | Proposta pendente, em analise. |
| `AND`, `ANDAMENTO` | `andamento` | Proposta em andamento, em analise. |
| `REP`, `REPROVADA` | `reprovada` | Proposta reprovada; exige observar motivo quando disponivel. |
| Outro valor | texto em lowercase | Situacao desconhecida; reportar como fato, sem inferir. |

## Politica operacional de elegibilidade

A politica default considera uma proposta elegivel quando todas as condicoes
abaixo sao verdadeiras:

- situacao esta em `BPO_ELIGIBLE_SITUATIONS`;
- `tipoProposta` esta em `BPO_ELIGIBLE_PROPOSAL_TYPES`;
- `limiteSaque > 0` quando `BPO_REQUIRE_POSITIVE_WITHDRAW_LIMIT=true`.

Nao relaxe essa regra sem ordem explicita. Para operar outro produto, carteira ou
cliente, ajuste essas variaveis em vez de alterar o codigo do agente.

## CPF

- Entrada aceita com ou sem pontuacao, mas deve normalizar para 11 digitos.
- Saida humana deve mascarar CPF, por exemplo `123.***.***-01`.
- JSON tambem deve passar por sanitizacao antes de ser entregue a outros agentes.

## Documentos anexados

- `Nao_Definido` e o tipo default quando o operador nao informa
  `--document-type`.
- `CCB_Negociavel` aparece como tipo real conhecido nos testes.
- O agente consulta metadados: nome, tipo, extensao, tamanho e presenca de
  ArquivoBase64/file_base64.
- O agente nao interpreta conteudo binario. Base64 deve ser redigido em saidas
  humanas e JSON sanitizado.

## Fatos e inferencias

- Observacoes retornadas pela BPO sao fatos.
- `processing_status.status == false` e fato de falha de processamento BPO.
- Ausencia de documentos e fato; possivel pendencia de formalizacao e inferencia.
- Reprovacao registrada por `motivoReprovacao` e fato; causa operacional exige
  analise humana ou dados adicionais.
