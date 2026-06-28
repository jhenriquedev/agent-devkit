# Regras

- Validar XML parseavel e raiz `mxfile` antes de avaliar qualidade visual.
- Tratar conector sem source ou target existente como erro bloqueante.
- Tratar node sem label ou geometria posicionada como erro bloqueante.
- Reportar sobreposicao, conectores sem label, titulo ausente e legenda ausente como warnings ou falhas conforme contexto.
- Conferir se perguntas abertas e fontes rastreadas continuam explicitas quando spec for fornecida.
- Nao alterar o `.drawio`; esta capability e read-only.
