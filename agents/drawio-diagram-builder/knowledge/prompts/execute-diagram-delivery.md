OBJETIVO: Orquestrar pacote ponta a ponta (ingestão→análise→geração→revisão→entrega).

ENTRADAS: fontes (text/file/directory/url), azure-card (opcional), generation args,
output-dir (obrigatório).

RACIOCÍNIO:
1. Ingerir fontes (+ card Azure se --azure-card foi informado).
2. Construir spec via build_specialized_spec.
3. Se spec.open_questions não vazio → delivery_status=needs_answers: emita
   diagram-interview.md e delivery-status.json, PARE antes de declarar entrega
   final. Não gere o .drawio até as perguntas serem respondidas.
4. Se delivery_status=ready → gere os 6 artefatos: source-context.json,
   diagram-plan.md, diagram-spec.json, diagram.drawio, diagram-review.md,
   open-questions.md.
5. Rode review automático (validate_drawio). Se erros bloqueantes → registre em
   diagram-review.md e delivery-status.

RUBRICA/REGRAS DE DECISÃO:
- Pergunte antes de criar o diretório de saída (--yes-create-dir).
- Pergunte antes de sobrescrever arquivos existentes (--yes-overwrite).
- Nunca declarar "pronto" quando delivery_status=needs_answers.

SAÍDA: source-context.json, diagram-plan.md, diagram-spec.json, diagram.drawio,
diagram-review.md, open-questions.md, delivery-status.json.

NÃO FAZER: declarar "pronto" quando delivery_status=needs_answers; criar diretório
sem confirmação; gerar pacote sem revisar o .drawio gerado.
