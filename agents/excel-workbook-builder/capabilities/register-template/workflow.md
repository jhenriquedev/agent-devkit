# register-template

OBJETIVO: Registrar um template .xlsx externo existente no catálogo local de
templates, criando o manifest e estrutura de versão inicial.

ENTRADAS: --template-id (slug obrigatório); --template (caminho .xlsx
obrigatório); --version (ex: 1.0.0); --name; --templates-root; --yes-save.

RACIOCÍNIO:
1. Valide que --template-id é um slug válido (sem espaços ou caracteres especiais).
2. Confirme que o template-id não está já registrado (list-templates).
3. Confirme gravação com o usuário antes de executar (write_policy:
   confirm); só prossiga com --yes-save ou confirmação explícita.
4. Crie a estrutura: templates/<id>/versions/<version>/ + template.yaml.
5. Inspecione o .xlsx registrado e registre o sheet-map inicial.

REGRAS DE DECISÃO:
- Sem --yes-save ou confirmação: não grava nada.
- template-id duplicado: falhe com erro claro.
- O template registrado permanece com status "draft" até promoção explícita.

SAÍDA: estrutura de template criada; manifest gerado; confirmação de registro.

NÃO FAZER: não promover automaticamente; não sobrescrever registros existentes.
