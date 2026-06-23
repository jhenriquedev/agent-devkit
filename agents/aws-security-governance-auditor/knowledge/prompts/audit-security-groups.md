# Capability: Auditar Security Groups (read-only)

## Objetivo
Detectar Security Groups com ingress aberto à internet (0.0.0.0/0 ou ::/0).

## Raciocínio
1. Para cada SG, percorrer IpPermissions.
2. Marcar achado quando houver IpRanges 0.0.0.0/0 ou Ipv6Ranges ::/0.
3. Escalar severidade se a porta exposta for de administração remota.

## Regras de decisão (rubrica)
- Porta 22 (SSH) ou 3389 (RDP) aberta ao mundo → critical.
- Qualquer outra porta/intervalo aberto ao mundo → high.
- Exposição interna (CIDR privado amplo) → medium (avaliar caso a caso).

## Saída
findings[] category=public-exposure, resource_type=security-group, com evidence
citando GroupName/GroupId, porta e CIDR.

## NÃO faça
Não recomende execução automática; sugira restringir a CIDRs/VPN/front-door gerenciado.
