# list-templates

OBJETIVO: Listar todos os templates registrados no diretório de templates,
com id, nome, versão atual e status.

ENTRADAS: --templates-root (opcional, default: templates/).

RACIOCÍNIO:
1. Varre templates/<id>/template.yaml para cada template registrado.
2. Extrai id, name, current_version, e status de cada manifest.
3. Formata a lista em markdown ou JSON (se --json).

REGRAS DE DECISÃO:
- Se não houver templates registrados, retorne lista vazia com mensagem clara.
- Não falhe silenciosamente se um template.yaml estiver malformado; reporte.

SAÍDA (markdown ou JSON): lista de templates com id, name, current_version,
versões disponíveis e status.

NÃO FAZER: não modificar nada; não ler template-catalog.yaml (fonte é
templates/*/template.yaml).
