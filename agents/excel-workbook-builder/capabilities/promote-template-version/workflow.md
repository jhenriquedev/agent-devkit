# promote-template-version

OBJETIVO: Marcar uma versão de template como "validated" e defini-la como
current_version no manifest.

ENTRADAS: --template-id (obrigatório); --template-version (obrigatório);
--templates-root.

RACIOCÍNIO:
1. Inspecione a versão com inspect-template ou compare-template-versions
   antes de promover.
2. Confirme com o usuário que a versão foi aprovada (write_policy: confirm).
3. Atualize o manifest: status="validated", current_version=<version>.
4. Registre o motivo de promoção no changelog.

REGRAS DE DECISÃO:
- Só promova com confirmação explícita do usuário.
- Verifique que a versão existe no manifest antes de promover.
- Manter versões antigas disponíveis (não deletar).

SAÍDA: manifest atualizado; changelog registrado.

NÃO FAZER: não promover sem inspeção prévia; não apagar versões anteriores.
