# Prompt: Identify Critical Points

## OBJETIVO
Identificar e documentar pontos críticos funcionais e técnicos que podem
bloquear, degradar ou introduzir risco na implementação da demanda.

## ENTRADAS
- `input`: análise de projeto, documentos intermediários ou demanda. Obrigatório.
- `focus`: área de foco opcional (ex.: segurança, desempenho, integração).

## PASSOS DE RACIOCÍNIO
1. Leia o input e identifique candidatos a ponto crítico em cada dimensão:
   - Funcional: regras de negócio ambíguas, fluxos sem tratamento de exceção,
     jornadas sem critério de aceite claro.
   - Técnico: débito técnico impactante, ausência de testes, integrações
     frágeis, ausência de rollback, migrações destrutivas.
   - Segurança: dados sensíveis sem proteção, permissões indefinidas,
     ausência de auditoria.
   - Dados: entidades sem ownership claro, inconsistências de schema,
     retenção indefinida de dados sensíveis.
   - Dependências externas: terceiros sem SLA documentado, APIs sem versionamento.
2. Para cada ponto crítico identificado, registre:
   - Evidência: onde foi observado (arquivo, regra, fluxo).
   - Rotulação: `FATO OBSERVADO` | `INFERÊNCIA`.
   - Impacto: qual o risco se não for tratado (alto/médio/baixo).
   - Ação recomendada: o que deve ser feito ou perguntado.
3. Ordene por impacto decrescente.

## FORMATO DE SAÍDA
- **critical-points.md**: tabela `Ponto Crítico | Tipo | Evidência | Rotulação |
  Impacto | Ação Recomendada`, ordenada por impacto, seguida de lista de
  perguntas derivadas para validação.

## NÃO FAÇA
- Não marque como `FATO OBSERVADO` o que é apenas suspeita.
- Não omita ponto crítico por ser desconfortável de reportar.
- Não propor solução técnica definitiva — apenas ação recomendada ou pergunta.
