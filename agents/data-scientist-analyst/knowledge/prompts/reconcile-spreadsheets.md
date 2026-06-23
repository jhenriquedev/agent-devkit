# reconcile-spreadsheets

## Objetivo
Conciliar duas bases tabulares por chave e tolerancia numerica, classificando
cada divergencia com motivo objetivo e sem mascarar discrepancias.

## Entradas
- `--left` (obrigatorio): caminho da planilha/arquivo esquerdo.
- `--right` (obrigatorio): caminho da planilha/arquivo direito.
- `--key` (obrigatorio): coluna(s) chave de juncao (simples ou composta).
- `--compare-columns`: colunas a comparar alem da chave.
- `--numeric-tolerance`: tolerancia para diferencas numericas (default 0.0).
- `--sheet`: aba para arquivos XLSX.

## Raciocinio
1. Confirme sha256 de ambas as fontes e registre no bloco de rastreabilidade.
2. Declare regras explicitamente: chave usada, colunas comparadas, tolerancia.
3. Execute juncao; classifique cada registro:
   - "so na esquerda" (ausente na direita),
   - "so na direita" (ausente na esquerda),
   - "divergente" (valor fora da tolerancia),
   - "status divergente" (campo categorico diferente),
   - "conciliado" (dentro da tolerancia).
4. Para CPF/CNPJ: normalize formato antes de comparar (remove pontuacao).
5. Reporte totais por categoria.

## Rubrica de decisao
- Divergencia sem motivo classificado -> nao reporte como "ok".
- sha256 ausente de qualquer fonte -> resultado inutilizavel.
- PII em colunas divergentes -> mascare nos exemplos.

## Saida
Totais (conciliados, divergentes por tipo), tabela das principais divergencias
(chave, coluna, valor_left, valor_right, motivo) com PII mascarado, regras
usadas, bloco de rastreabilidade (ambas as fontes).

## Nao fazer
- Nao mascarar divergencias (todas devem aparecer).
- Nao exibir PII integral nas divergencias.
- Nao gerar relatorio sem --output.
