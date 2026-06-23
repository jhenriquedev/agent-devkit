# map-source-to-template

OBJETIVO: Mapear colunas da fonte de dados para campos/abas do template,
produzindo um mapping.yaml que guia a geração do workbook.

ENTRADAS: --source-schema (JSON ou caminho do normalized-data.json);
--template-id; --template-version; --field source=target (repetível, mapeia
explicitamente); --templates-root.

RACIOCÍNIO:
1. Carregue o sheet-map da versão do template alvo.
2. Para cada coluna da fonte, tente correspondência: primeiro pelos mapeamentos
   explícitos (--field), depois por similaridade de nome (slug normalizado).
3. Identifique: mapped_columns, unmapped_source_columns,
   unfilled_template_fields (obrigatórios sem origem).
4. Se campos obrigatórios do template ficarem unmapped, pergunte ao usuário
   antes de continuar.

REGRAS DE DECISÃO:
- Campos obrigatórios sem origem = bloqueante: não gere workbook.
- Sugestões de mapeamento automático devem ser apresentadas como rascunho
  para aprovação, não aplicadas silenciosamente.

SAÍDA: mapping.yaml com source→target por aba + relatório de lacunas.

NÃO FAZER: não inventar mapeamentos; não silenciar campos obrigatórios sem
origem.
