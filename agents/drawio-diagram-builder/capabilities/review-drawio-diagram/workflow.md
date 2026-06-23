# Workflow: Review Drawio Diagram

OBJETIVO: Validar um .drawio contra todos os quality_gates de policies.yaml e
traduzir resultados em ações corretivas.

ENTRADAS: diagram (arquivo .drawio).

RACIOCÍNIO:
1. Parse o XML; verificar raiz mxfile e presença de página.
2. Validar cada gate de policies.yaml:
   - xml_parseavel: XML sintaxe correta?
   - raiz_mxfile_presente: tag raiz é mxfile?
   - pagina_drawio_presente: existe diagram > mxGraphModel > root?
   - nos_com_labels: todos os nós de conteúdo têm value não vazio?
   - conectores_com_source_e_target_existentes: source/target existem?
   - geometria_nao_sobreposta: nós sem sobreposição geométrica?
   - titulo_presente: mxCell id="diagram-title" existe?
   - legenda_quando_necessaria: legenda quando content_vertices > 4 ou > 1 grupo?
3. Para cada ERRO → descreva a correção necessária na spec.
4. Para cada AVISO → descreva o impacto e se a correção é recomendada.

DECISÃO: Qualquer error[] bloqueia a entrega; não declarar "pronto" com erros.

SAÍDA: diagram-review.md com seções Erros / Avisos / Quality Gates / Ações
Corretivas.

NÃO FAZER: declarar diagrama válido quando há errors[]; verificar apenas
subconjunto dos gates.
