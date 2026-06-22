# Load Support Context

## Fluxo

1. Ler fixture quando informada.
2. Carregar contrato N1 de `--n1-contract` ou da fixture.
3. Carregar card Azure quando `--project` e `--card` existirem.
4. Renderizar card de fixture quando houver `work_item`.
5. Extrair entidades do texto consolidado.
6. Inferir sintoma a partir de supportContext, titulo e descricao.
7. Coletar evidencias de supportContext, checks e diagnostic gaps N1.
8. Validar handoff com `validate_handoff`.

## Saida

Retorna contexto estruturado para as demais capabilities N2.
