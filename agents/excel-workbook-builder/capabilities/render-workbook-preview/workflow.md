# render-workbook-preview  (DEPENDE DO RUNTIME NODE)

OBJETIVO: Renderizar uma imagem de preview (.png) de abas ou ranges críticos
do workbook para conferência visual antes da entrega.

ENTRADAS: --workbook (obrigatório); --sheet; --range (ex: A1:H20); --output.

RACIOCÍNIO:
1. PRÉ-CHECK do runtime Node (ver runtime.md).
2. Se Node indisponível: registre o gap no relatório; não bloqueie os outros
   gates (review e scan são Python puros e devem rodar mesmo sem preview).
3. Renderize a(s) aba(s) ou range(s) especificado(s) como imagem.
4. Verifique legibilidade: cortes, áreas vazias, dados fora do range visível.
5. Reporte ajustes necessários de layout/zoom.

REGRAS DE DECISÃO:
- Para workbooks GERADOS pelo agente, o preview é obrigatório pela policies.yaml.
- Se Node ausente: documente o gap explicitamente; não entregue workbook sem
  ao menos review + scan terem passado.

SAÍDA: preview.png no caminho --output.

NÃO FAZER: não substituir review e scan pelo preview; não modificar o workbook.
