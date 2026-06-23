# validate-source-data

OBJETIVO: Validar dados normalizados contra um schema esperado (colunas
obrigatórias, tipos, unicidade) antes de gerar qualquer workbook.

ENTRADAS: --input (JSON normalizado obrigatório); --expected-schema (JSON com
required_columns[], types{col:type}, unique[]).

RACIOCÍNIO:
1. Verifique colunas obrigatórias: presença de todas as required_columns.
2. Verifique tipos: cada coluna em types{} deve ter o tipo declarado.
3. Verifique unicidade: nenhuma duplicata nas colunas em unique[].
4. Classifique cada falha como bloqueante (missing_column, wrong_type,
   duplicate) ou aviso (null_excess, extra_columns).

REGRAS DE DECISÃO:
- Qualquer erro bloqueante = status: fail; NÃO prossiga para geração.
- Avisos não bloqueiam, mas devem ser reportados.
- Se expected-schema não for fornecido, reporte aviso e valide só estrutura.

SAÍDA (markdown + JSON): validation-report.md com status pass/fail, erros
bloqueantes e avisos.

NÃO FAZER: não modificar os dados; não gerar workbook com status: fail.
