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

RUBRICA/REGRAS DE DECISÃO:
- Nunca inventar exceções, handoffs ou decisões não citadas na fonte.
- Se a sequência não estiver clara → registrar como open_question, não inventar ordem.
- Aplique preset 'product' de templates/style-presets.yaml.

SAÍDA: flow.drawio + diagram-spec.json com diagram_type="flowchart" (ou subtipo
específico: user_journey, runbook, etc.).

NÃO FAZER: inventar exceções/handoffs não citados; omitir rótulos de ramos de
decisão; usar leitura de cima para baixo em fluxo de processo.
