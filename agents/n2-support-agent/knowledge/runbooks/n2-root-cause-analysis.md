# N2 Root Cause Analysis

## Ordem operacional

1. Carregar contrato N1 ou card Azure.
2. Validar se o handoff contem entidades, checks, gaps e decisao.
3. Ler codigo do projeto quando `codebase_path` for informado.
4. Relacionar evidencias runtime com arquivos e metodos relevantes.
5. Classificar causa raiz.
6. Gerar `patch_plan.md` com TDD, atividades, arquivos, criterios de aceite e
   migrations quando necessario.
7. Preparar comentario tecnico para o card.
8. Planejar ou executar tags, movimento, comentario e anexo no Azure.

## Criterios

- Sem destino de `patch_plan.md` e sem card Azure, o N2 deve pedir destino.
- Sem informacao suficiente para patch seguro, o plano deve listar perguntas
  bloqueantes.
- O N2 nao implementa o patch.
