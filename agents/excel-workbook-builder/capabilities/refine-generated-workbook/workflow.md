# refine-generated-workbook  (DEPENDE DO RUNTIME NODE)

OBJETIVO: Aplicar feedback estruturado em um workbook gerado, produzindo
uma versão refinada sem destruir a estrutura validada.

ENTRADAS: --workbook (obrigatório); --feedback (texto descritivo ou JSON com
mudanças específicas); --output.

RACIOCÍNIO:
1. Leia o feedback e classifique cada item: layout, fórmula, dados, formatação.
2. Para cada item, planeje a mudança mínima necessária.
3. PRÉ-CHECK do runtime Node.
4. Aplique as mudanças preservando fórmulas e estrutura fora do escopo.
5. Execute quality gates completos após o refinamento.

REGRAS DE DECISÃO:
- Feedback vago ("melhorar visual"): confirme com o usuário o que
  especificamente mudar antes de aplicar.
- Mudanças que afetam fórmulas dependentes: execute scan-formula-errors
  após aplicar.

SAÍDA: workbook.xlsx refinado no caminho --output.

NÃO FAZER: não aplicar feedback destrutivo sem confirmar; não pular os gates
após refinar.
