# normalize-tabular-data

OBJETIVO: Padronizar dados tabulares extraídos (nomes de colunas, tipos,
encoding) antes de validar ou gerar workbook.

ENTRADAS: --input (JSON tabular obrigatório); --slug-columns (slugificar
nomes com acento/espaço); --output.

RACIOCÍNIO:
1. Leia o JSON tabular de entrada.
2. Padronize nomes de colunas: lowercase, sem espaços/acentos (se
   --slug-columns); nunca destrua identificadores textuais como CPF/CNPJ.
3. Infira tipos básicos (número, texto, data) sem forçar conversão destrutiva.
4. Reporte: duplicidades de coluna, nulos excessivos, conversões aplicadas.

REGRAS DE DECISÃO:
- Numéricos que chegam como texto formatado ("1.234,56") devem ser
  convertidos e o campo original registrado.
- Nunca silenciar duplicatas; reportar como aviso.
- Não inferir tipos se a coluna tiver conteúdo ambíguo — manter como texto
  e reportar.

SAÍDA: normalized-data.json + relatório de normalização .md.

NÃO FAZER: não inventar colunas; não silenciar duplicatas; não destruir IDs.
