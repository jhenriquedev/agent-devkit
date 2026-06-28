# Decision Rules

- Gerar comentario interno, resposta ao cliente e pacote N2 a partir da decisao e evidencias ja coletadas.
- Nunca incluir CPF cru, tokens, credenciais, connection strings ou dumps completos de log.
- A resposta ao cliente deve conter linguagem objetiva e apenas informacao apropriada ao solicitante.
- O comentario interno deve separar fatos, inferencias, lacunas e proximas acoes.
- O pacote N2 deve incluir rota, checks executados, evidencias, lacunas e criterio de escalonamento.
- Se a decisao for `needs_more_info`, formular pedido de informacao minimo e objetivo.
- Se houver pendencia operacional N1, nao gerar escalonamento como se fosse falha tecnica.
- Se houver falha tecnica confirmada, incluir ids de correlacao e janela temporal suficientes para agrupamento.
- Nao prometer correcao ou prazo sem evidencia no contrato de entrada.
- Manter os artefatos coerentes com `qualityGate`, `diagnosticGaps` e `azureActions`.
