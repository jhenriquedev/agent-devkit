# Prompt — ingest-design-source

## OBJETIVO
Extrair contexto de UI/UX de documentos e pastas e produzir inventario inicial rastreavel.

## ENTRADAS
- `--source`: arquivos (.md/.txt/.json/.yaml/.html/.css/.js/.ts/.tsx/.pdf/.docx/.xlsx) ou pastas.
- `--brief`: descricao resumida do projeto (complementa as fontes).

## RACIOCINIO (passos)
1. Consolide as fontes resumidas; note o tipo de cada arquivo e limitacoes de leitura.
2. Extraia entidades relevantes: personas, fluxos, telas mencionadas, restricoes, regras, riscos.
3. Derive telas/areas provaveis e componentes a partir das fontes; cite a referencia (SRC-xxx) para cada item.
4. Marque lacunas: o que o material nao cobre que e necessario para desenhar.
5. Aplique `depth-scope-rules.md` para sugerir profundidade e escopo com base no volume/qualidade das fontes.

## REGRAS DE DECISAO
- PDFs sem extrator disponivel → inventarie o arquivo, avise sobre limitacao e peca conversao (conforme `policies.yaml` unsupported_binary_policy).
- Toda tela ou componente listado deve citar a fonte (SRC-xxx) ou ir para perguntas abertas com rotulo "A confirmar".
- Fontes contraditórias entre si → registre o conflito em open-design-questions.md; nao decida sozinho.

## SAIDA
- `design-brief.md`: objetivo, publico, plataforma, escopo extraidos das fontes.
- `screen-inventory.md`: telas identificadas com objetivo e referencias de fonte.
- `source-traceability.md`: mapa fonte → informacoes extraidas.
- `open-design-questions.md`: lacunas e conflitos identificados.

## NAO FACA
- Nao trate inferencia heuristica como fato; rotule claramente como "A confirmar".
- Nao ignore formatos nao suportados silenciosamente; avise sempre.
