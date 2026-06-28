# Decision Rules: Analyze Workload Architecture

## Objetivo de decisao

Isolar um workload dentro do inventario AWS e produzir uma leitura de
componentes, entrypoints, compute, storage, mensageria, rede, IAM e perguntas
abertas.

## Entradas minimas

- `--inventory` deve apontar para inventario valido.
- Informar `--workload` ou `--resource-prefix` quando a analise nao for da conta
  inteira.
- Quando nenhum filtro for informado, declarar explicitamente que a analise
  considera todos os recursos do inventario.

## Quando executar

Execute quando:

- o usuario quer entender um sistema, produto, servico ou prefixo dentro da
  conta AWS;
- ha inventario local suficiente para separar componentes;
- a saida esperada e analitica, nao uma operacao AWS.

Nao execute quando:

- o inventario ainda nao foi coletado;
- o filtro retorna zero recursos e o usuario espera uma conclusao arquitetural;
- o pedido exige consultar AWS real adicional sem passar pela coleta.

## Regras de filtragem

1. Filtrar por nome ou id de recurso usando `workload` ou `resource_prefix`.
2. Nao assumir que prefixo parcial cobre todo o workload; registrar pergunta
   aberta.
3. Agrupar recursos por papel arquitetural quando possivel, mas separar fatos de
   inferencias.
4. Nao inferir criticidade, owner ou ambiente se tags/metadados nao existirem.
5. Quando o filtro retornar poucos recursos, declarar que a visao pode estar
   incompleta.

## Criterios de qualidade

- `workload-components.json` contem recursos filtrados e contagem por servico.
- `workload-architecture.md` descreve componentes encontrados e lacunas.
- `workload-open-questions.md` lista owners, criticidade, limites do filtro e
  dependencias fora do inventario.
- Saida humana nao afirma completude sem evidencia.

## Escalacao

Pedir refinamento de filtro quando:

- multiplos workloads aparecem misturados;
- recursos criticos esperados nao aparecem;
- tags de ambiente, owner ou produto estao ausentes.
