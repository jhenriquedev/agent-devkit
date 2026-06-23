# Prompt — capture-url-to-figma

## OBJETIVO
Capturar URL, localhost ou web app autorizado como referencia no Figma ou gerar plano de captura.

## ENTRADAS
- `--source`: URL a capturar (proprio, localhost ou autorizado).
- `--brief`: contexto de uso da captura.
- `--figma-file-url`: arquivo Figma existente onde inserir (opcional).
- `--yes-figma-write`: confirmacao para escrita real.

## RACIOCINIO (passos)
1. Confirme a permissao: URL propria, localhost ou explicitamente autorizada? Se for produto de terceiro sem autorizacao, pare e registre em open-design-questions.md.
2. Detecte modo Figma; se `plan_only`, gere instrucoes de captura manual.
3. Em `direct_mcp` + `--yes-figma-write`:
   - Use skill `figma-generate-design` com `capture_url_to_figma`; capture a URL como referencia.
   - Crie frame editavel a partir da captura; aplique tokens do design system se disponivel.
   - Capture node IDs / file_url retornados.
4. Gere inventario do que foi capturado e identifique componentes a componentizar.

## REGRAS DE DECISAO
- Clone pixel-perfect de produto de terceiro sem permissao: PROIBIDO.
- URL propria/localhost/autorizada: permitido com confirmacao de escrita.
- Sem `--yes-figma-write`: gere somente plano de captura.
- Sem evidencia do bridge: NAO afirme que a captura foi executada no Figma.

## SAIDA
- `figma-action-plan.md`, `screen-inventory.md`.
- Em `direct_mcp`: `+ figma-execution-result.json`, `design-operation-log.md`.

## NAO FACA
- Nao prossiga sem confirmar permissao de captura.
- Nao afirme captura Figma sem evidencia do bridge.
