# Prompt — read-azure-card-for-design

## OBJETIVO
Preparar contexto de design a partir de um card Azure DevOps, delegando leitura ao
azure-devops-orchestrator/read-card via CLI raiz.

## ENTRADAS
- `--azure-card`: identificador do card Azure DevOps (ID ou URL).
- `--source`: fontes adicionais opcionais.
- `--output-dir`: pasta de saida.

## RACIOCINIO (passos)
1. Verificar se a delegacao esta disponivel:
   - Disponivel: acionar `ai-devkit --json run azure-devops-orchestrator read-card --id <id>` e consumir o artefato retornado.
   - Indisponivel (sem CLI ou credenciais): declarar modo degradado, solicitar conteudo do card como arquivo/texto colado.
2. Extrair do card: objetivo/titulo, criterios de aceite, descricao, anexos, comentarios relevantes.
3. Gerar brief de design a partir do conteudo do card.
4. Identificar lacunas para UX: plataforma, publico, design system, estados obrigatorios.
5. Gerar perguntas abertas especificas para o card.

## REGRAS DE DECISAO
- NAO ler AZURE_DEVOPS_PAT diretamente no runner; a leitura deve ser sempre via delegacao ao orchestrator ou via conteudo fornecido pelo usuario.
- Comentar no card Azure exige confirmacao explicita (`--yes-comment-card`).
- Se a delegacao nao retornou conteudo real, NAO afirme ter lido o card; declare degradacao.

## SAIDA
- `azure-card-design-context.md`: contexto extraido do card com fonte "Azure Card #ID".
- `design-brief.md`: objetivo, criterios, plataforma, escopo.
- `open-design-questions.md`: lacunas identificadas.

## NAO FACA
- Nao afirme ter lido o card se a delegacao nao retornou conteudo.
- Nao altere o card sem confirmacao explicita.
- Nao use PAT diretamente no runner; delegue sempre.
