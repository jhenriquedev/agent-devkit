# Workflow: Analyze Diagram Context

OBJETIVO: Decidir o(s) diagrama(s) e produzir o diagram-spec.json correto.

ENTRADAS: source-context.json (ou fontes), diagram_type opcional, title, audience.

RACIOCÍNIO:
1. Classifique o objetivo e mapeie para uma FAMÍLIA da taxonomia
   (architecture | product | operations | data) e um tipo específico.
   Consulte knowledge/diagram-taxonomy.yaml para os tipos válidos por família.
2. Trate o spec rascunho de build_specialized_spec como ponto de partida: revise
   cada nó/aresta. Corrija labels longos, kinds errados, grupos sem sentido e
   arestas sem suporte na fonte.
3. Modele cada nó com: id estável, label curto (<= ~8 palavras), group por
   camada/ator/sistema/domínio, kind (process|decision|actor|database|entity),
   description = trecho-fonte que o justifica.
4. Modele arestas só quando a relação existe na fonte; rotule quando carrega
   ação/evento/decisão/protocolo/payload.
5. Separe facts | assumptions | open_questions claramente.
6. Decida 1 vs N diagramas: se node_count > 12 OU > 2 responsabilidades distintas
   OU mistura de famílias → recomendar split em páginas/diagramas.

DECISÃO: Se faltar dimensão bloqueante → emita open_questions e NÃO finalize a spec.

SAÍDA: diagram-spec.json (conforme schema) + diagram-plan.md.

NÃO FAZER: criar nó para algo não suportado pela fonte; deixar aresta apontando
para id inexistente; aceitar o rascunho regex como spec final sem revisão.
