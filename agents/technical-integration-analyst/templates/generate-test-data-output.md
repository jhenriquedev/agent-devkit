# Massa de Testes

## {METHOD} {/path}

### Valida

```json
{"id": "{{resource_id}}", "name": "valid-test"}
```

### Invalida

```json
{"missing_required_field": true}
```

### Limite

```json
{"max_length_text": "xxx...255chars", "zero_amount": 0}
```

### Dependente de Fluxo

```json
{"id": "{{resource_id_criado_pelo_POST_anterior}}"}
```

<!-- Repita o bloco acima para cada operacao detectada no contrato.
     Sem operacoes = "Nenhuma operacao detectada para gerar massa."
     Casos "Dependente de Fluxo" aparecem quando o contrato inclui flow. -->
