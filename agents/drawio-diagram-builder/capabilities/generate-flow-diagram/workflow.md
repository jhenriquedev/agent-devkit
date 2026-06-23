# Workflow: Generate Flow Diagram

OBJETIVO: Gerar fluxograma (jornada, processo, runbook, incidente, decisão, estado,
exceção).

ENTRADAS: brief, fontes ou spec; output path.

RACIOCÍNIO:
1. Ordene passos pela sequência da fonte (não invente ordem).
2. Identifique kind=decision para construções "se/caso/quando/caso contrário";
   senão kind=process.
3. Agrupe por raia: Usuario | Sistema | Fluxo (conforme quem executa cada passo).
4. Leitura esquerda→direita.
5. Rotule transições; nomeie ramos de decisão (sim/não, aprovado/reprovado).

DECISÃO: Nunca inventar exceções, handoffs ou decisões não citadas na fonte.

SAÍDA: flow.drawio + diagram-spec.json com diagram_type="flowchart".

NÃO FAZER: inventar exceções/handoffs não citados; omitir rótulos de ramos de
decisão; usar leitura de cima para baixo em fluxo de processo.
