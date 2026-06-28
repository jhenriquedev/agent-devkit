# Decision Rules: Estimate Blast Radius

## Objetivo de decisao

Estimar impacto direto e indireto de falha, remocao ou alteracao em um recurso
AWS, usando inventario e mapa de dependencias.

## Entradas minimas

- `--resource-id` e obrigatorio.
- `--inventory` deve apontar para inventario valido.
- `--dependency-map` deve ser usado quando ja existir; se ausente, pode ser
  reconstruido a partir do inventario.

## Quando executar

Execute quando:

- o usuario quer avaliar impacto antes de uma mudanca ou incidente;
- o recurso alvo existe no inventario;
- dependencias diretas e indiretas podem ser calculadas ou lacunas podem ser
  declaradas.

Nao execute quando:

- o recurso alvo nao existe no inventario; pare e reporte erro;
- o usuario quer executar a mudanca de fato;
- dependencias nao resolvidas podem tornar o resultado inutil sem nova coleta.

## Regras de impacto

1. Recurso alvo nao encontrado deve bloquear conclusao; nao retornar impacto
   vazio como seguro.
2. Dependentes diretos tem prioridade sobre indiretos.
3. Dependencias `inferred` reduzem confianca do impacto.
4. Dependencias nao resolvidas relacionadas ao alvo devem declarar que o impacto
   pode estar subestimado.
5. Acoes inseguras devem ser listadas explicitamente.
6. Nao recomendar remocao, reboot, scale down ou alteracao sem validacao humana.

## Criterios de qualidade

- `blast-radius.json` contem alvo, recurso, dependentes diretos, indiretos e
  contadores.
- `blast-radius.md` lista impactos e acoes inseguras em linguagem operacional.
- Incertezas aparecem no artefato quando ha dependencia inferida ou nao
  resolvida.
- Resultado separa fato do mapa de dependencia de inferencia do agente.

## Escalacao

Pedir nova coleta ou revisao humana quando:

- alvo pertence a workload critico;
- existem dependencias nao resolvidas;
- o resultado sera usado para mudanca em producao.
