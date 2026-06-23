# list-template-versions

OBJETIVO: Listar todas as versões de um template específico com status, data
de criação e notas.

ENTRADAS: --template-id (obrigatório); --templates-root.

RACIOCÍNIO:
1. Leia o manifest templates/<template-id>/template.yaml.
2. Liste cada versão com: version, status, path, created_at, notes.
3. Destaque a current_version.

REGRAS DE DECISÃO:
- Se o template-id não existe, falhe com mensagem acionável.
- Se o manifest tiver versões sem created_at, exiba-as com campo vazio.

SAÍDA (markdown): tabela de versões com version, status, created_at, notes.

NÃO FAZER: não modificar manifest; não misturar com list-templates.
