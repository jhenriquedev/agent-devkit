# Draw.io Diagram Builder

Agente especialista em criar diagramas `.drawio` completos, detalhados,
entendiveis e visualmente organizados a partir de fontes reais.

## Escopo

- entrevistar o usuario quando faltar contexto;
- ingerir arquivos, pastas, texto, specs e cards Azure;
- planejar diagramas adequados ao objetivo e audiencia;
- gerar `.drawio` editavel;
- revisar qualidade tecnica e visual;
- refinar iterativamente ate a entrega estar validada.

O ciclo de entrega usa `diagram-spec.json` como contrato intermediario. As
capabilities especializadas geram specs proprias para arquitetura, fluxos e ERD;
o refinamento altera a spec e re-renderiza o `.drawio`.

## Uso

```bash
./ai-devkit capabilities drawio-diagram-builder
./ai-devkit run drawio-diagram-builder conduct-diagram-interview --brief "Fluxo de onboarding"
./ai-devkit run drawio-diagram-builder ingest-diagram-sources --directory specs --output source-context.json
./ai-devkit run drawio-diagram-builder generate-drawio-diagram --brief "Usuario compra produto e sistema confirma pagamento" --output checkout.drawio
./ai-devkit run drawio-diagram-builder generate-architecture-diagram --brief "Cliente acessa app. App chama API. API grava no Postgres." --output arquitetura.drawio --spec-output arquitetura.json
./ai-devkit run drawio-diagram-builder generate-erd-diagram --brief "Tabela cliente possui id nome. Tabela pedido possui id cliente_id valor." --output erd.drawio --spec-output erd.json
./ai-devkit run drawio-diagram-builder execute-diagram-delivery --file spec.md --diagram-type flowchart --output-dir diagrams --yes-create-dir
```

## Tipos de diagrama

- arquitetura de software;
- C4 context/container/component;
- arquitetura cloud;
- integracoes e APIs;
- fluxos de produto;
- jornadas de usuario;
- service blueprint;
- runbooks e fluxos operacionais;
- incidentes e escalonamento;
- ERD e linhagem de dados;
- arvores de decisao;
- estados e transicoes.

## Guardrails

- O agente gera arquivos locais e nao altera sistemas externos.
- Leitura de Azure DevOps e feita por delegacao read-only.
- O `.drawio` e gerado em XML nao comprimido para facilitar diff e revisao.
- Lacunas bloqueantes viram perguntas antes da entrega final.
- Quando houver perguntas abertas, `execute-diagram-delivery` gera
  `diagram-interview.md` e `delivery-status.json` com `needs_answers`.
