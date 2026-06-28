# Decision Rules

- Comparar apenas versoes existentes do mesmo `template_id`.
- Ler manifests, `slide-map.yaml`, schemas de entrada, usage notes e changelog quando disponiveis.
- Separar diferencas estruturais, visuais, de schema e de status.
- Nao alterar manifests, arquivos de template ou status durante a comparacao.
- Destacar impactos de compatibilidade para decks ja gerados.
- Sinalizar campos removidos, renomeados ou obrigatorios adicionados como breaking changes.
- Nao assumir equivalencia visual apenas porque os arquivos existem.
- Preservar paths portaveis e relativos ao template.
- Registrar lacunas quando algum artefato versionado estiver ausente.
- A saida deve orientar promocao, depreciacao ou nova versao, sem executar essas acoes.
