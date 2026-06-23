# Prompt — generate-dev-handoff

## OBJETIVO
Gerar handoff acionavel para desenvolvimento com todas as especificacoes necessarias.

## ENTRADAS
- `--brief`: contexto do produto.
- `--source`: artefatos de design (screen-inventory, design-system-spec, telas Figma).
- `--figma-file-url`: arquivo Figma com os frames finais (opcional).

## RACIOCINIO (passos)
1. Consolide: frames principais e seus objetivos, todos os estados cobertos por tela, componentes e tokens utilizados.
2. Para cada tela: descreva regras de interacao (o que acontece ao clicar X, hover, foco), microcopy (textos de botao, placeholder, mensagem de erro, empty state), transicoes e animacoes.
3. Liste perguntas abertas que o dev nao pode assumir sozinho.
4. Se houver arquivo Figma com bridge: inclua links/node IDs dos frames principais.
5. Verifique criterios de acessibilidade (`accessibility-rules.md`): anote quais precisam de implementacao especifica (aria-label, foco, contraste).

## REGRAS DE DECISAO
- Nao instrua implementar regra aberta sem confirmacao; registre como pergunta.
- Se nao houver node IDs Figma, documente o handoff sem eles (nao e bloqueio).

## SAIDA
- `dev-handoff.md`: frames, estados, componentes, tokens, regras de interacao, microcopy, perguntas abertas, links Figma.

## NAO FACA
- Nao instrua o dev a assumir regras de negocio nao confirmadas.
- Nao omita estados de erro ou empty state do handoff.
