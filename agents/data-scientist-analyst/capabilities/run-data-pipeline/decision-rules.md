# Regras

- Exigir `output` para gerar pacote de artefatos reproduziveis.
- Encadear ingestao, perfil, exploratoria e relatorio sem modificar a fonte.
- Registrar fonte, hash, parametros, regras aplicadas e limites de leitura.
- Mascarar dados pessoais em todos os artefatos humanos.
- Se uma etapa falhar, manter erro rastreavel e nao inventar resultado das etapas seguintes.
- Nao chamar sistemas externos diretamente; usar somente repositories e agentes declarados.
