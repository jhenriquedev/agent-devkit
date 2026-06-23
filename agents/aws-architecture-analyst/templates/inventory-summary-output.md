# AWS Inventory Summary

> Contrato de saida: capability `discover-account-inventory`

## Escopo
- **Account:** `{account_id}`
- **Region:** `{region}`
- **Profile:** `{profile}`
- **Fonte:** `real | fixture`
- **Coletado em:** `{generated_at}`

## Servicos e Contagem
| Servico | Recursos |
|---|---|
| lambda | N |
| ec2 | N |
| sqs | N |
| ... | ... |

**Total:** N recursos

## Lacunas de Coleta
Servicos do escopo MVP nao cobertos por esta coleta:
- `{servico}`: motivo / collector ausente / erro
- ...

> NOTA: "0 recursos" != "servico nao usado". Servicos sem collector nao foram
> verificados e devem ser listados aqui como lacuna, nao como ausencia confirmada.

---
*Separacao: os campos acima sao FATOS (retornados pela AWS ou pela fixture).
Qualquer inferencia sobre o ambiente deve ser rotulada explicitamente.*

