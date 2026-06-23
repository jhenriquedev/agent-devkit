# Prompt — review-design-quality

## OBJETIVO
Revisar qualidade visual, UX e acessibilidade do design e gerar relatorio com status por gate.

## ENTRADAS
- `--source`: artefatos do design (brief, screen-inventory, design-system-spec, dev-handoff).
- `--figma-file-url`: arquivo Figma a revisar (opcional; aciona `review_file` no bridge).
- `--brief`: contexto.

## RACIOCINIO (passos)
1. Para cada gate do `design-quality-checklist.md`, avalie: pass / needs_input / planned.
2. Execute tambem os gates de `accessibility-rules.md`:
   - Contraste de texto >= 4.5:1 (normal) / 3:1 (grande).
   - Alvo de toque >= 44px (iOS) / 48dp (Android) / 24px (web AA 2.2).
   - Foco visivel em todos os elementos interativos.
   - Labels em todos os campos e botoes icone.
   - Erros descritos textualmente (nao so por cor).
3. Verifique cobertura de estados: vazio, loading, erro, sucesso, permissao em cada tela.
4. Verifique responsividade (web) / safe area e frames (mobile).
5. Verifique reuso de design system e consistencia de tokens.
6. Se houver arquivo Figma em `direct_mcp`: acione `review_file` no bridge para obter screenshot e metadata atualizados.

## REGRAS DE DECISAO
- NAO marque "pass" em execucao Figma sem evidencia do bridge (file_url / node IDs).
- Gate "needs_input": registre o que falta em open-design-questions.md.
- Gate "planned": deve ter item correspondente em figma-action-plan.md.

## SAIDA
- `design-quality-report.md`: tabela de gates com status e observacoes.
- `open-design-questions.md`: perguntas derivadas de gates needs_input.

## NAO FACA
- Nao marque gate como pass sem verificar.
- Nao ignore gates de acessibilidade.
