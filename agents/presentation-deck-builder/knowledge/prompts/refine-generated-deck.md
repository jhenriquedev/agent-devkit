# Prompt: refine-generated-deck

## OBJETIVO
Aplicar feedback do usuario ao deck gerado, produzindo uma nova versao do arquivo
.pptx sem sobrescrever o original.

## ENTRADAS
- `--deck` (obrigatorio): caminho do deck .pptx original.
- `--feedback` (obrigatorio): descricao das mudancas solicitadas.
- `--output` (opcional): caminho do novo deck; se ausente, sufixo `-refined`.

## RACIOCINIO (passos)
1. Interpretar o feedback em mudancas concretas e especificas:
   - Mudancas de texto: qual campo, qual valor novo.
   - Mudancas de ordem: quais slides reordenar.
   - Mudancas de enfase: negrito, destaque, tamanho.
2. Preservar identidade visual e restricoes do template.
3. Re-renderizar como NOVO arquivo de saida (nao sobrescrever original sem pedido).
4. Se o feedback pedir mudancas de identidade visual sem pedido explicito: alertar
   e perguntar ao usuario.

## RUBRICA / REGRAS DE DECISAO
- Identidade visual: preservar a menos que o usuario peca explicitamente alterar.
- Sem sobrescrever o original: gerar sempre em caminho novo ou com sufixo.
- Se feedback for ambiguo: perguntar antes de aplicar.

## SAIDA
- Novo deck .pptx refinado.
- Resumo das mudancas aplicadas (lista de itens alterados).

## NAO FACA
- Nao introduza conteudo nao pedido pelo usuario.
- Nao quebre a identidade do template.
- Nao sobrescreva o original sem confirmacao.
