# Decision Rules: Review Networking

## Objetivo de decisao

Revisar topologia de rede, VPCs, subnets, route tables, load balancers, security
groups e exposicao publica a partir de inventario AWS.

## Entradas minimas

- `--inventory` deve apontar para inventario valido.
- O inventario deve conter atributos de rede necessarios para avaliar exposicao,
  como `public_ip`, security groups, subnets e load balancers quando aplicavel.

## Quando executar

Execute quando:

- o usuario quer identificar exposicoes, lacunas ou riscos de topologia;
- ha inventario local suficiente para revisar rede;
- a saida esperada e diagnostico read-only.

Nao execute quando:

- o usuario pede alterar security group, route table ou subnet;
- o pedido e auditoria profunda de seguranca, que pertence ao
  `aws-security-governance-auditor`;
- os atributos de rede nao foram coletados e a conclusao seria especulativa.

## Regras de classificacao

1. IP publico confirmado em EC2 e pelo menos `medium`, salvo contexto explicito
   de bastion/public edge.
2. Ausencia do atributo `public_ip` e `gap`, nao "privado".
3. Regras administrativas abertas para `0.0.0.0/0` devem ser `medium` ou `high`
   conforme porta e criticidade.
4. Load balancer internet-facing nao e automaticamente problema, mas deve ser
   marcado como exposicao a validar.
5. Nao inferir isolamento de rede sem subnet/route table/security group
   coletados.

## Criterios de qualidade

- `networking-findings.json` lista achados com severidade e confianca.
- `networking-review.md` separa exposicoes confirmadas, riscos potenciais e
  lacunas.
- Toda lacuna informa qual atributo ou collector precisa ser ampliado.
- Nenhuma saida recomenda mutacao direta; recomendacoes sao planos de revisao.

## Escalacao

Sinalizar ao humano quando:

- recurso sensivel aparece publicamente exposto;
- porta administrativa esta aberta para internet;
- a topologia de producao nao pode ser avaliada por falta de atributos de rede.
