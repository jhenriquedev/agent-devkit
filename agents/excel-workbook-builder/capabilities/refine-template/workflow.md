# refine-template

OBJETIVO: Criar uma nova versão de template incorporando feedback, sem
sobrescrever a versão validada base.

ENTRADAS: --template-id (obrigatório); --version (nova versão obrigatória);
--base-version (obrigatório); --feedback (descrição do refinamento);
--templates-root.

RACIOCÍNIO:
1. Leia o feedback e identifique mudanças de layout, formulas, validações
   e schemas necessárias.
2. Crie nova versão baseada em --base-version.
3. Registre o feedback no changelog da nova versão.
4. Solicite aprovação antes de promover.

REGRAS DE DECISÃO:
- O template validado de base nunca é alterado in place.
- Feedback sem versão explícita: confirme a nova versão com o usuário.

SAÍDA: nova versão criada (igual a create-template-version com feedback).

NÃO FAZER: não sobrescrever versão validada; não promover automaticamente.
