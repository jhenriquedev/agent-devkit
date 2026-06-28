# Regras

- Operar em modo read-only; nunca escrever artefatos durante inspecao.
- Usar a heuristica de `recommended_profile` como ponto de partida, nao como veredito final.
- Recomendar `business-domain`, `integration-docs` ou `support-operations` explicitamente quando sinais fortes justificarem.
- Registrar arquivos ignorados, PDFs sem texto, fonte heterogenea e limites de leitura como riscos.
- Usar paths relativos ao source root ou `repo://<project-id>/...` quando houver project id.
- Nao inventar conteudo de arquivos nao lidos.
