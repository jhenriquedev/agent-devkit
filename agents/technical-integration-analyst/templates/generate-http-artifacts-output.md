# Artefatos HTTP

## Curl

```bash
curl --request GET \
  '{{base_url}}/resource' \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer {{token}}'
```

```bash
curl --request POST \
  '{{base_url}}/resource' \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer {{token}}' \
  --header 'Content-Type: application/json' \
  --data '{"example": "value"}'
```

<!-- Um bloco curl por operacao HTTP detectada. Methods nao-seguros incluem Content-Type e body. -->

## Postman Collection

Arquivo JSON salvo em `{postman_output_path}` quando `--postman-output` for fornecido.
Schema: https://schema.getpostman.com/json/collection/v2.1.0/collection.json

Variables configuradas na collection:
- `base_url`: {base_url | {{base_url}}}
- `token`: (preencher com credencial segura)
- `resource_id`: (preencher apos operacao de criacao)
