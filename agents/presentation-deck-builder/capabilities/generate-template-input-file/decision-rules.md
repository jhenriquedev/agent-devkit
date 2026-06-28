# Decision Rules

- Resolver `template_id` e versao antes de gerar schemas.
- Ler `slide-map.yaml` como fonte principal dos campos esperados.
- Gerar `input-schema.xlsx` e `input-schema.md` coerentes entre si.
- Nao alterar `template.pptx` ao gerar arquivo de entrada.
- Preservar tipos, obrigatoriedade, exemplos e descricoes de cada campo.
- Quando placeholders estiverem ambiguos, registrar lacuna em vez de inventar campo.
- Para template validado, escrever schema somente como artefato da versao correta.
- Manter paths relativos e portaveis dentro da pasta do template.
- Nao remover campos existentes sem nova versao ou decisao explicita.
- A saida deve permitir preenchimento pelo usuario sem consultar o slide-map manualmente.
