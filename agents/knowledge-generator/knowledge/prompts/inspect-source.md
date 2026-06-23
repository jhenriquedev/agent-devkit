# Prompt: Inspect Source

## Objetivo
Classificar uma fonte local e recomendar um profile, SEM escrever artefatos.

## Entradas
- `source` (obrigatorio): path de arquivo ou pasta.
- `profile` (opcional, default `auto`), `project_id` (opcional).
A capability retorna: `source.languages`, `source.content_kinds`,
`source.signals` (api/database/frontend/support/business/integration),
`source.ignored`, previews por arquivo, `recommended_profile`.

## Passos de raciocinio
1. Leia `recommended_profile` (heuristica do corpo) como ponto de partida — NAO
   como veredito final.
2. Cruze com `signals` e previews para decidir o profile real:
   - `business` (regra/processo/jornada/ator/decision) dominante em docs -> `business-domain`.
   - `integration` (soap/rest/sftp/webhook/token/payload/contrato) -> `integration-docs`.
   - `support` (runbook/troubleshooting/symptom/incident/playbook) -> `support-operations`.
   - codigo com linguagens backend -> `code-project`.
   - apenas linguagens frontend (dart/html/css/ts/js) -> `frontend-app`.
   - dados/schemas/planilhas predominantes -> `data-domain`.
   - so documentos -> `documentation-set`.
   - mais de um tipo forte sem dominante -> `mixed-knowledge`.
   - fonte pequena/ambigua -> `freeform`.
3. Observe `ignored_count`: se alto, sinalize que parte da fonte nao foi lida.

## Regras de decisao
- A heuristica do corpo NUNCA escolhe `business-domain`/`integration-docs`/
  `support-operations` sozinha. Se os sinais apontarem para um deles, voce DEVE
  recomendar `--profile <esse>` explicito ao gerar.
- Se discordar de `recommended_profile`, declare o profile sugerido e o porque.

## Saida
- Profile recomendado (e alternativo).
- Justificativa por sinais/linguagens/conteudo.
- Riscos: arquivos ignorados, PDFs sem texto, fonte heterogenea.

## NAO fazer
Nao escreva artefatos. Nao invente conteudo de arquivos nao lidos.
