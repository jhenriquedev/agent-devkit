# explain-reconciliation-differences

OBJETIVO: Traduzir diferenças de conciliação em explicações executivas e
técnicas, identificando causas prováveis por classe de diferença.

ENTRADAS: --reconciliation-summary (JSON obrigatório); --reconciliation-data
(JSON com detalhes); --output.

RACIOCÍNIO:
1. Carregue reconciliation-rules.md.
2. Para cada classe (matched/different/left_only/right_only), explique:
   - Causa provável da diferença (timing, chave duplicada, dado ausente,
     arredondamento, tolêrancia).
   - Impacto no negócio (registros afetados, valor monetário se aplicável).
3. Produza explicação executiva (resumo) e técnica (detalhe por registro/coluna).

REGRAS DE DECISÃO:
- Diferenças "within_tolerance" devem ser explicadas com a tolerância usada.
- Causas incertas: use linguagem condicional ("provavelmente", "suspeito de").

SAÍDA (markdown): difference-explanation.md com seções Executivo e Técnico.

NÃO FAZER: não aplicar ajustes; não omitir classes com 0 registros.
