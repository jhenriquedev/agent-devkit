# Decision Rules: List Log Groups

- Exigir `region` quando nao houver `fixture`.
- Aplicar `log_group_prefix` quando informado e preservar o prefixo na saida.
- Avisar quando prefixo estiver ausente porque a descoberta pode ficar ampla.
- Nao consultar eventos nesta capability; ela apenas descobre log groups.
- Nao inferir saude, trafego ou impacto pela existencia de um log group.
- Manter limite explicito e tratar nomes de log groups como dados operacionais sensiveis.
