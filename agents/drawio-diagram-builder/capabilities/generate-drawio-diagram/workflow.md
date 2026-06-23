# Workflow: Generate Drawio Diagram

OBJETIVO: Renderizar um diagram-spec.json em arquivo .drawio XML não comprimido.

ENTRADAS: spec (arquivo JSON) ou fontes para construir spec; output path.

RACIOCÍNIO:
1. Se spec foi fornecida via --spec: carregue e valide contra
   templates/diagram-spec.schema.json antes de renderizar.
2. Se spec não foi fornecida: construa a partir das fontes via build_specialized_spec
   (rascunho determinístico) — revise nós/arestas.
3. Renderize via render_drawio(spec) → XML.
4. Valide o XML gerado (validate_drawio): qualquer erro bloqueante exige correção
   da spec antes de entregar.

DECISÃO: Spec inválida contra o schema ou XML com errors[] → corrigir antes de
entregar.

SAÍDA: diagram.drawio (XML), diagram-spec.json (spec usada), diagram-notes.md.

NÃO FAZER: entregar .drawio sem validar; ignorar erros de schema; sobrescrever
arquivo existente sem --yes-overwrite.
