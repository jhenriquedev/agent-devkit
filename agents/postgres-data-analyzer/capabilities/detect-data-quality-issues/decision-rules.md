# Decision Rules: Detect Data Quality Issues

- Detectar problemas por consultas read-only e agregacoes limitadas.
- Avaliar nulos, brancos, duplicidades, baixa cardinalidade, formato suspeito e valores extremos.
- Usar thresholds versionados em `knowledge/policies.yaml` quando aplicavel.
- Nao corrigir, deletar, deduplicar ou normalizar dados.
- Evitar exibir valores pessoais brutos; preferir contagens e exemplos mascarados.
- Separar problema confirmado, suspeita e limitacao da amostra.
- Registrar colunas analisadas e colunas puladas por risco ou permissao.
- Recomendar validacoes adicionais sem propor mutacao direta.
