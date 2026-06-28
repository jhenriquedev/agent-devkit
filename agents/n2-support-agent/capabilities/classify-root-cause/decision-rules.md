# Decision Rules

- Classificar somente nas categorias versionadas da taxonomia N2.
- Usar `backend_bug` quando houver erro tecnico e arquivo de codigo candidato localizado.
- Usar `data_inconsistency` quando a evidencia apontar divergencia entre banco, estado ou persistencia.
- Usar `external_provider_issue` quando BPO, provider ou fornecedor explicar melhor o sintoma.
- Usar `customer_pending_action` quando a continuidade depender de documento, aceite, formalizacao ou dado do cliente.
- Usar `insufficient_evidence` quando faltarem codigo candidato, runtime evidence ou handoff suficiente.
- `readyForImplementation` so pode ser verdadeiro com confianca >= `0.65` e categoria diferente de `insufficient_evidence`.
- Listar evidencias, contradicoes e lacunas separadamente.
- Nao promover hipotese fraca a causa raiz por conveniencia de plano.
- Manter PII mascarada e segredos fora da explicacao.
