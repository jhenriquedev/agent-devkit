# Prompt: inspect-template

## OBJETIVO
Descrever layouts, placeholders, tipos de slide, identidade visual e campos
obrigatorios de uma versao de template, produzindo `template-inspection.md`.

## ENTRADAS
- `--template-id` (obrigatorio): identificador do template.
- `--template-version` (opcional): versao alvo; default = `current_version`.

## RACIOCINIO (passos)
1. Resolver a versao alvo via template-routing: id+version -> usa essa versao;
   so id -> usa `current_version`; template inexistente -> reportar e parar.
2. Ler `slide-map.yaml` da versao: id do slide, proposito, required_fields.
3. Ler `usage-notes.md` para orientacoes de preenchimento.
4. (Quando runner disponivel) Abrir o .pptx e listar layouts, placeholders, fontes
   e cores da identidade visual.
5. Mapear `required_fields` x placeholders por slide; registrar alertas.
6. Escrever `template-inspection.md`.

## RUBRICA / REGRAS DE DECISAO
- Versao inexistente: erro imediato com lista das versoes disponiveis.
- Alertas nao bloqueiam a inspecao; sao listados na secao de alertas.
- Identidade visual = "nao disponivel" se .pptx nao puder ser lido.

## SAIDA (template-inspection.md)
Tabela: | slide_id | slide | purpose | layout | placeholders | required_fields |
Secao "Identidade Visual": fonte(s), cores, layout base.
Secao "Alertas": placeholders sem campo, campos sem placeholder.

## NAO FACA
- Nao altere o template nem o slide-map.
- Nao invente placeholders inexistentes.
- Nao gere deck aqui.
