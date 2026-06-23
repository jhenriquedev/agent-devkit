# Prompt — create-figma-project

## OBJETIVO
Criar novo projeto Figma com estrutura de paginas base e configuracao inicial.

## ENTRADAS
- `--brief`: descricao do projeto.
- `--source`: fontes de referencia.
- `--platform`: web | mobile | both.
- `--figma-file-name`: nome do arquivo Figma a criar.
- `--yes-figma-write`: flag de confirmacao para escrita real no Figma.
- `--require-direct`: exige bridge ativo; para se nao disponivel.

## RACIOCINIO (passos)
1. Detecte o modo Figma; se `blocked`, pare e explique o que falta no ambiente.
2. Classifique profundidade e escopo a partir do brief/fontes (aplicar `depth-scope-rules.md`).
3. Planeje a estrutura do arquivo:
   - Paginas: Discovery, Design System, Flows, Screens, Review, Handoff.
   - Breakpoints conforme plataforma (ver `ux-patterns.md`).
4. Em `direct_mcp` com `--yes-figma-write`: acione bridge com `create_new_file`; capture `file_key` e `file_url`.
5. Em `plan_only`: gere `figma-action-plan.md` detalhado com instrucoes passo a passo.
6. Gere design-brief.md com decisoes tomadas e perguntas abertas.

## REGRAS DE DECISAO
- Criacao de arquivo Figma exige `--yes-figma-write`; sem ele, gere somente plano.
- Sem evidencia (`file_key`/`file_url`) retornada pelo bridge, NAO afirme que o arquivo foi criado.

## SAIDA
- `design-brief.md`, `figma-action-plan.md`, `open-design-questions.md`.
- Em `direct_mcp`: `+ figma-execution-result.json`, `design-operation-log.md`.

## NAO FACA
- Nao afirme criacao Figma sem evidencia real do bridge.
- Nao pule confirmacao de escrita.
