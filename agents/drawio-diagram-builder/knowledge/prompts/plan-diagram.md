OBJETIVO: Produzir plano auditável antes de gerar o diagrama.

ENTRADAS: brief ou source-context, diagram_type opcional, title.

RACIOCÍNIO:
1. A partir da spec (ou do brief), declare: título, tipo, audiência, nível de
   detalhe, nº de nós/arestas previsto, escopo e fora de escopo.
2. Liste elementos obrigatórios que não podem faltar no diagrama final.
3. Liste os quality_gates que serão verificados no review (de policies.yaml).
4. Separe o que é fato observado, o que é premissa e o que é pergunta aberta.

RUBRICA/REGRAS DE DECISÃO:
- O plano é um artefato auditável — não pode ser vago.
- Se o escopo não estiver claro, registre como pergunta aberta e sinalize que o
  plano é preliminar.

SAÍDA: diagram-plan.md com seções: Título / Tipo / Audiência / Nível de detalhe /
Fontes analisadas / Nós previstos / Conectores previstos / Fora de escopo /
Elementos obrigatórios / Fatos / Premissas / Perguntas Abertas / Quality Gates.

NÃO FAZER: omitir o fora-de-escopo; prometer gates que o review não checa; confundir
premissas com fatos.
