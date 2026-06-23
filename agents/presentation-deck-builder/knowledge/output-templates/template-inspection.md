# Template Inspection: <template-id> <version>

> Gerado por: inspect-template
> Template: <template-id>
> Versao: <version>
> Status: <draft|validated|deprecated>
> Data: <data>

## Slides

| slide_id | slide | purpose | layout | placeholders | required_fields |
|---|---|---|---|---|---|
| cover | 1 | abertura | <layout> | title, subtitle, date | title, subtitle, date |
| content-01 | 2 | conteudo | <layout> | slide_title, bullets | slide_title, bullets |
| closing | 3 | fechamento | <layout> | next_steps | next_steps |

## Identidade Visual

- Fonte(s): <nome da fonte ou "nao disponivel">
- Cores principais: <lista de cores hex ou "nao disponivel">
- Layout base: <descricao ou "nao disponivel">
- Tamanho do slide: <largura x altura ou "nao disponivel">

## Alertas

| tipo | slide_id | descricao |
|---|---|---|
| ALERTA | <slide_id> | placeholder X nao tem campo em required_fields |
| ALERTA | <slide_id> | campo Y nao tem placeholder correspondente |

---
> Fatos (fonte): lidos de slide-map.yaml e usage-notes.md.
> Inferencias (agente): correspondencia placeholder x required_field.
