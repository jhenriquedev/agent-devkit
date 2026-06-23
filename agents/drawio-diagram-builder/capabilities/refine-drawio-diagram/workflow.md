# Workflow: Refine Drawio Diagram

OBJETIVO: Aplicar feedback ao diagrama preservando o que já está bom.

ENTRADAS: diagram (arquivo .drawio), feedback (texto), spec original (--spec,
OBRIGATÓRIO para refinamento semântico).

RACIOCÍNIO:
1. SEMPRE carregue a spec original via --spec. Sem a spec, o conteúdo do diagrama
   (nós/arestas) é perdido — nunca refine sem spec contra diagrama com conteúdo.
2. Interprete o feedback além de renomeie/adicione/remova: reagrupar, religar
   arestas, mudar kind, dividir em páginas, ajustar legenda.
3. Preserve IDs quando possível para manter rastreabilidade.
4. Re-renderize e re-valide via validate_drawio. Gere changelog item a item.

DECISÃO: Se o feedback for ambíguo → pergunte antes de aplicar mudança destrutiva.
Spec ausente + diagrama com conteúdo real → recusar operação, solicitar --spec.

SAÍDA: diagram.drawio refinado + diagram-spec.refined.json + diagram-changelog.md.

NÃO FAZER: rodar refino sem --spec contra diagrama com conteúdo; descartar nós
não citados no feedback; aplicar mudança destrutiva ambígua sem confirmação.
