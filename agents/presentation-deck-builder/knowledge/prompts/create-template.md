# Prompt: create-template

## OBJETIVO
Criar um template novo quando o usuario nao fornece um arquivo .pptx, produzindo
um template draft estruturado a partir de um brief.

## ENTRADAS
- `--brief` (obrigatorio): descricao do objetivo, publico e estilo do template.
- `--template-id` (opcional): identificador desejado.
- `--audience` (opcional): publico-alvo.
- `--style` (opcional): estilo visual.

## RACIOCINIO (passos)
1. PERGUNTAR ao usuario: objetivo da apresentacao, publico, estilo visual,
   numero de slides e campos obrigatorios — antes de criar qualquer arquivo.
2. Propor uma estrutura (slide-map) e identidade visual baseada nas respostas.
3. Aguardar confirmacao explicita do usuario antes de criar.
4. Apos confirmacao: criar `template.pptx` (draft minimo), `template.yaml`,
   `slide-map.yaml`, `input-schema.xlsx/.md`, `usage-notes.md`, `changelog.md`.
5. Marcar como `draft` — nunca `validated` automaticamente.

## RUBRICA / REGRAS DE DECISAO
- `confirm`: nao crie nenhum arquivo sem confirmacao.
- Nunca reutilize identidade visual de outro template sem pedido explicito.
- Nunca marque como `validated` automaticamente.
- Se brief for muito vago: perguntar ate ter informacao suficiente.

## SAIDA
- `template.pptx` (draft minimo), `template.yaml`, `input-schema.xlsx/.md`.
- Resumo da estrutura: slides, campos obrigatorios, identidade proposta.

## NAO FACA
- Nao reutilize identidade de outro template sem pedido.
- Nao gere deck aqui.
- Nao promova para `validated`.
