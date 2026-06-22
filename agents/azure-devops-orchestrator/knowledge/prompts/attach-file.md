# Prompt: Anexar Arquivo ao Card

Objetivo: anexar um arquivo local a um work item, com confirmacao antes da
escrita real.

Entradas esperadas: work_item_id, project e file com path local existente;
comment opcional; --execute para escrita real.

Passos de raciocinio:

1. Valide que o arquivo existe localmente.
2. Leia o card alvo.
3. Em dry-run, renderize plano com path, nome do arquivo e comentario.
4. Apos confirmacao e --execute, faca upload e adicione a relacao AttachedFile
   via update-work-item; reporte attachment_url e new_rev.

Regras de decisao:

- Nao anexe arquivo inexistente.
- Nao anexe dados sensiveis sem solicitacao explicita do usuario.
- Confirme antes de escrever.
- Sem --execute, gere apenas o plano de escrita.

Formato de saida: use templates/attach-file-output.md, com Target, File, Result
e Confirmation.

NAO faca: nao escreva sem --execute; nao envie arquivos fora do path informado;
nao duplique dados sensiveis no comentario.
