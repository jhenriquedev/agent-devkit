# deprecate-template-version

OBJETIVO: Marcar uma versão de template como "deprecated" impedindo seu uso
em novas gerações, sem apagar arquivos históricos.

ENTRADAS: --template-id (obrigatório); --template-version (obrigatório);
--templates-root.

RACIOCÍNIO:
1. Confirme com o usuário que a versão não deve ser usada (write_policy: confirm).
2. Atualize o manifest: status="deprecated".
3. Se a versão era current_version, limpe current_version (deixa vazio).
4. Registre o motivo no changelog.

REGRAS DE DECISÃO:
- Só deprecie com confirmação explícita.
- Nunca apague arquivos históricos automaticamente.

SAÍDA: manifest atualizado; changelog registrado.

NÃO FAZER: não apagar arquivos; não depreciar sem confirmação.
