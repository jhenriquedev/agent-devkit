# Decision Rules: Audit Secrets Usage

## Objetivo de decisao

Auditar metadados de Secrets Manager sem ler valores secretos, identificando
ausencia de rotacao detectada.

## Entradas minimas

- Snapshot deve conter `secrets.secrets`.
- Em AWS real, `region` deve estar resolvida para `list-secrets`.
- Nunca chamar API de leitura de valor secreto.

## Quando executar

Execute quando:

- o usuario quer revisar governanca de secrets;
- ha metadados de Secrets Manager disponiveis;
- a saida esperada e recomendacao de rotacao ou justificativa.

Nao execute quando:

- o usuario pede valor do secret;
- o pedido exige alterar secret, rotation lambda ou policy;
- a region nao foi coletada e o usuario espera conclusao definitiva.

## Regras de classificacao

1. `RotationEnabled` ausente ou falso e `medium` com `status: potential`.
2. Nao avaliar conteudo, forca ou validade de senha.
3. Nome/ARN do secret pode aparecer; valor secreto nunca.
4. Ausencia de metadado e lacuna, nao evidencia de rotacao.
5. Long-lived credential deve ser recomendado para rotacao ou justificativa
   documentada.

## Criterios de qualidade

- `secrets-usage-audit.json` contem findings com `resource_type: secret`.
- `secrets-usage-audit.md` nao contem secret value.
- Evidencia usa apenas metadados.
- Recomendacao nao executa rotacao automaticamente.

## Escalacao

Pedir revisao humana quando secret parecer de producao, banco de dados,
integracao externa, credencial compartilhada ou sem owner claro.
