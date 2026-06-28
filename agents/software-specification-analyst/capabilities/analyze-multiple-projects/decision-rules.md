# Decision Rules

- Validar todos os paths de projeto antes de iniciar a analise.
- Classificar profundidade `light`, `medium` ou `deep` conforme quantidade de projetos, criticidade e incerteza.
- Ignorar diretorios gerados, dependencias, caches e vendor conforme `knowledge/policies.yaml`.
- Separar fatos observados em cada projeto de inferencias sobre regra de negocio.
- Mapear fronteiras, ownership, contratos, APIs, eventos, dados compartilhados e pontos de acoplamento.
- Registrar divergencias entre projetos como perguntas ou riscos, nao como decisao final.
- Nao criar especificacao final quando houver regra implicita ou ownership nao confirmado.
- Preservar paths portaveis e relativos quando listar arquivos.
- Levantar perguntas de negocio e arquitetura para validar impactos cross-project.
- Antes de criar diretorio de saida, pedir confirmacao conforme write policy.
