# Vendor

Esta pasta contem conteudo externo, importado ou vendorizado que pode ser usado
pelo Agent DevKit, mas nao representa agentes especialistas do projeto.

## Objetivo

Manter skills, plugins e bundles de terceiros separados dos agentes nativos.
Agentes podem depender desse conteudo, mas devem declarar essa dependencia em
seus manifests.

## Estrutura atual

```text
vendor/
├─ skills/
└─ plugins/
```

## Regras

- Nao edite conteudo vendorizado sem motivo claro.
- Se uma capability depender de algo em `vendor/`, declare essa dependencia no
  `agent.yaml` ou `capability.yaml`.
- Conteudo que passar a ser propriedade do DevKit deve ser migrado para o agente
  dono ou para uma capability especifica.
