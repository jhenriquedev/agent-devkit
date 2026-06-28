# Decision Rules

- Revisar readiness sem escrever ou anexar `patch_plan.md`.
- Validar destino de entrega: `--output` ou card Azure.
- Validar existencia de contrato N1 ou contexto Azure suficiente.
- Validar arquivo candidato e estrategia de reproducao.
- Validar categoria de causa raiz e confianca minima conforme taxonomia.
- Bloquear implementacao quando a categoria for `insufficient_evidence`.
- Bloquear quando houver diagnostic gaps que mudem a causa raiz provavel.
- Consolidar perguntas bloqueantes em linguagem objetiva e acionavel.
- Nao mascarar readiness como aprovado quando houver apenas hipotese.
- Retornar `readyForImplementation` coerente com blockers, qualidade do plano e evidencias.
