# Prompt: Discover Account Inventory

## Objetivo
Coletar inventario AWS read-only com escopo explicito e normaliza-lo, registrando
o que foi coletado e o que ficou de fora.

## Entradas esperadas
- profile, region, account_id (opcionais; region obrigatoria para servicos
  regionais), OU uma fixture JSON.
- output_dir + flags de confirmacao.

## Passos de raciocinio
1. Confirme o escopo. Se region faltar e a coleta for real, pare e peca — nao
   assuma uma regiao silenciosamente.
2. Rode a descoberta (allowlist read-only). Cada collector que falhar vira uma
   entrada em `gaps` — nao engula erros.
3. Apos coletar, compare os servicos retornados com o escopo MVP de
   knowledge/context.md. Servicos do escopo que nao foram coletados sao LACUNAS,
   nao ausencias confirmadas.
4. Resuma: total de recursos, por servico, account, region, fonte (real|fixture).

## Regras de decisao
- "0 recursos de um servico" != "servico nao usado". Marque como lacuna se o
  collector nao cobre aquele servico.
- Single-region por padrao: sempre declare a regiao analisada e que outras
  regioes NAO foram varridas.

## Formato de saida
- inventory.json (schema normalizado), inventory-summary.md, collection-metadata.json.
- No summary, secao "Lacunas de coleta" listando servicos do escopo nao cobertos.

## Nao faca
- Nao varra todas as regioes. Nao imprima credenciais/secrets. Nao afirme
  cobertura total. Nao mute nada.
