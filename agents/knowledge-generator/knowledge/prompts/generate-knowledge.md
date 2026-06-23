# Prompt: Generate Knowledge

## Objetivo
Gerar uma pasta `knowledge/` por profile, com fatos rastreaveis, inferencias
marcadas e lacunas explicitas — pronta para ser `default_context` de outro agente.

## Entradas
- `source` (obrigatorio), `output_dir` (opcional), `profile` (default `auto`),
  `project_id` (opcional), `yes_create_dir`, `yes_overwrite`.

## Passos de raciocinio
1. Rode `inspect-source` antes (ou use seu resultado). Confirme o profile.
2. Verifique escrita: se `output_dir` nao existe e falta `--yes-create-dir`,
   PARE e peca confirmacao; para sobrescrever, exija `--yes-overwrite`.
3. Gere o esqueleto (o corpo cria project/source-index/inventarios/coverage/gaps).
4. ENRIQUECA os artefatos de dominio (nao deixe so termos frequentes):
   - `domain.json`: extraia regras de negocio, atores, processos e decisoes como
     itens estruturados `{id, type: rule|actor|process|decision, summary,
     evidence, source, status: fact|inference}`.
   - `integration.json`: extraia contratos `{id, protocol, endpoint|operation,
     auth, payload_shape, errors, source, status}`.
   - `operations.json`: extraia playbooks `{id, symptom, evidence, steps,
     source, status}`.
   - `document-map.json`/`code-inventory.json`: confira headings/simbolos e
     anote os relevantes.
5. Para CADA item: cite `source` (path relativo) e classifique como `fact`
   (afirmado na fonte) ou `inference` (deduzido por voce).
6. Popule `hardening/initial-gaps.json` com lacunas REAIS (campos sem evidencia,
   PDFs sem texto, profile sem codigo, secao incompleta), nao so o gap generico.
7. Rode `validate-knowledge` e corrija ate `valid:true`.

## Regras de decisao (rubrica fato/inferencia/lacuna)
- `fact`: a fonte afirma literalmente (regra escrita, contrato documentado).
- `inference`: voce deduziu de codigo/estrutura; marque e justifique.
- `gap`: a fonte nao cobre o campo -> registre, nao preencha com suposicao.
- Seguranca: ao topar com segredo, garanta mascaramento e adicione gap de
  seguranca; nunca persista o valor bruto.

## Saida
Pasta `knowledge/` com os `required_artifacts` do profile + artefatos de dominio
enriquecidos. Resumo final: profile, n.o de fatos vs inferencias, top lacunas.

## NAO fazer
- Nao gere campos vazios "para preencher o template".
- Nao use paths absolutos nos artefatos.
- Nao sobrescreva sem `--yes-overwrite`.
