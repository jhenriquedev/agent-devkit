# export-workbook-artifacts

OBJETIVO: Empacotar o workbook final e artefatos relacionados (review, scan,
preview, mapping) para entrega ao usuário.

ENTRADAS: --workbook (obrigatório); --output-dir; --include-review; --include-
preview; --include-mapping.

RACIOCÍNIO:
1. Confirme que o workbook passou pelos quality gates: review-generated-workbook
   + scan-formula-errors devem ter retornado status: pass.
2. Reúna os artefatos solicitados na pasta --output-dir.
3. Gere um manifesto de entrega com caminhos absolutos e checksums.
4. Verifique que nenhum artefato tem status: fail antes de exportar.

REGRAS DE DECISÃO:
- Se review ou scan tiverem status: fail: recuse a exportação com erro claro.
- Se --include-preview mas o preview não existe: avise mas não bloqueie (Node
  pode estar ausente).
- Caminhos devem ser absolutos no manifesto.

SAÍDA: pasta --output-dir/ com workbook.xlsx e artefatos selecionados +
delivery-manifest.md.

NÃO FAZER: não exportar com status: fail; não incluir artefatos de runs
anteriores sem confirmar.
