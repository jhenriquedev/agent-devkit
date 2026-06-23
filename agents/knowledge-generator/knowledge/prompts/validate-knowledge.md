# Prompt: Validate Knowledge

## Objetivo
Validar uma pasta `knowledge/` gerada e decidir se esta pronta para uso.

## Entradas
- `knowledge_dir` (obrigatorio).
A capability retorna `{valid, profile, errors, warnings}`.

## Passos de raciocinio
1. Rode a validacao. Se `errors` nao vazio, liste o que falta (JSON invalido,
   `project.json` ausente, `required_artifacts` faltando).
2. Interprete `warnings` (ex.: `initial-gaps.json` sem gaps) como sinal de
   knowledge raso, nao como ok.
3. Para cada erro, indique a acao corretiva concreta (regerar com profile X,
   adicionar artefato Y, popular gaps).

## Regras de decisao
- `valid:true` + zero warnings relevantes = pronto.
- `valid:true` mas gaps vazios ou artefatos de dominio so com termos = NAO
  pronto para uso operacional; recomende re-geracao enriquecida.

## Saida
Status (pronto / precisa correcao) + lista de correcoes priorizadas.

## NAO fazer
Nao altere a pasta aqui; apenas avalie e recomende.
