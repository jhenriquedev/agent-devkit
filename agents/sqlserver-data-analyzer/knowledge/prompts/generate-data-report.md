# Prompt: generate-data-report

## OBJETIVO
Gerar um relatório consolidado do banco ou tabela: profile, problemas de
qualidade, colunas sensíveis e relacionamentos — separando dados coletados
de inferências.

## ENTRADAS
- `schema` (opcional): escopo do relatório.
- `table` (opcional): se fornecido junto com `schema`, inclui profile e
  quality_issues da tabela.

## RACIOCÍNIO (passos)
1. Execute a capability `generate-data-report`.
2. O runner coleta: `profile` (se schema+table), `quality_issues`
   (se schema+table), `sensitive_columns` e `relationships`.
3. Organize em seções separando **coletado** (banco) de **inferido**
   (heurística por nome).

## RUBRICA / REGRAS DE DECISÃO
- **Dados coletados:** profile stats, quality issues, relationships (FK real).
- **Inferências:** sensitive_columns classificadas por nome (pode ter falso
  positivo/negativo).
- Não inclua amostras de dados pessoais brutos — apenas métricas.
- Se schema sem table → relatório de banco (sem profile/quality por tabela).

## SAÍDA
Relatório com seções:
1. **Summary** — escopo, schema, tabela (se aplicável).
2. **Profile** (se table) — stats por coluna.
3. **Quality Issues** (se table) — issues detectados.
4. **Sensitive Columns (inferência)** — tabela coluna→kind + nota de inferência.
5. **Relationships** — FKs declaradas.

## NÃO FAÇA
- Não inclua amostras de dados pessoais brutos.
- Não apresente sensitive_columns como lista definitiva sem nota de inferência.
