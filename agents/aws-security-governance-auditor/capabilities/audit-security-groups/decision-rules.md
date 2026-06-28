# Decision Rules: Audit Security Groups

## Objetivo de decisao

Auditar regras de ingress de Security Groups com foco em exposicao ampla para a
internet.

## Entradas minimas

- Snapshot deve conter `security_groups`.
- Em AWS real, `region` deve estar resolvida para `describe-security-groups`.
- `--output-dir` deve existir ou receber `--yes-create-dir`.

## Quando executar

Execute quando:

- o usuario quer revisar regras de rede expostas;
- ha Security Groups coletados para uma regiao;
- a saida esperada e findings de risco, nao mudanca de regra.

Nao execute quando:

- o usuario quer editar ingress/egress;
- nao ha region para coletar Security Groups;
- o pedido exige analise completa de path de rede com route tables, NACL e ALB.

## Regras de classificacao

1. `0.0.0.0/0` ou `::/0` em porta 22 ou 3389 e `critical`.
2. `0.0.0.0/0` ou `::/0` em outra porta e `high`.
3. Porta ausente deve ser reportada como `all` na evidencia.
4. Nao inferir compensating control sem evidencia no snapshot.
5. Security Group sem regra publica nao gera finding por si so.

## Criterios de qualidade

- `security-groups-audit.json` contem findings com `resource_type:
  security-group`.
- Evidencia identifica group name/id, CIDR publico e porta.
- Recomendacao orienta restringir CIDR, VPN, rede privada ou front door
  gerenciado.
- Nenhum comando de mutacao e sugerido como executado.

## Escalacao

Sinalizar ao humano quando porta administrativa estiver aberta, quando SG
pertencer a producao ou quando o grupo estiver associado a dado sensivel.
