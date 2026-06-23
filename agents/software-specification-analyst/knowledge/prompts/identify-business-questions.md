# Prompt: Identify Business Questions

## OBJETIVO
Converter lacunas de documentos de análise ou código em perguntas objetivas e
acionáveis para os donos certos, organizadas por eixo e criticidade.

## ENTRADAS
- `input`: análise, demanda ou documentos de projeto. Obrigatório.
- `source_type`: `analysis` | `code` | `demand` (opcional).

## PASSOS DE RACIOCÍNIO
1. Liste cada lacuna, ambiguidade ou decisão pendente encontrada no input.
2. Para cada lacuna, formule UMA pergunta fechada o suficiente para ser
   respondida com sim/não ou uma resposta objetiva.
3. Classifique o eixo: `negócio` | `produto` | `dados` | `segurança` | `QA` |
   `arquitetura` (conforme `interview_policy.group_questions_by`).
4. Marque criticidade:
   - `bloqueante` — sem resposta, não é possível prosseguir.
   - `importante` — afeta qualidade da spec mas não bloqueia.
   - `nice-to-have` — melhora a spec mas pode ficar em aberto.
5. Identifique o dono sugerido: PO, tech lead, DBA, sec, QA, etc.
6. Ordene: bloqueantes primeiro, depois importantes, depois nice-to-have.

## RUBRICA DE QUALIDADE DE PERGUNTA
- Boa: "O usuário precisa aprovar manualmente cada transação acima de R$ 1.000?"
- Ruim: "Quais são os requisitos de aprovação?" (genérica demais)
- Ruim: "Isso funciona bem?" (retórica)

## FORMATO DE SAÍDA
Tabela com colunas: `Pergunta | Eixo | Por que importa | Criticidade |
Dono sugerido`, agrupada por eixo, bloqueantes primeiro em cada grupo.

## NÃO FAÇA
- Não faça pergunta retórica ou genérica ("o que mais?").
- Não esconda lacuna por parecer óbvia.
- Não formule mais de uma pergunta por lacuna (abra itens separados).
