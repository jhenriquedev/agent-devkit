# Scripts

Esta pasta contem automacoes operacionais do repositorio Agent DevKit como um todo.

## Objetivo

Guardar scripts globais que atuam sobre varios agentes ou sobre o ciclo de vida
do repositorio.

## Exemplos

- Validar todos os `agent.yaml`.
- Gerar catalogos globais a partir dos manifests dos agentes.
- Rodar checagens de consistencia em todos os agentes.
- Empacotar agentes para distribuicao.

## Scripts atuais

- `validate-repo.py`: valida estrutura de agentes, capabilities, runners,
  referencias internas, cobertura dos READMEs e higiene basica da raiz sem
  chamar rede, bancos, AWS, Azure ou qualquer sistema externo.
- `mvp-readiness.py`: executa um smoke gate local do MVP instalavel, com
  instalacao temporaria, backends LLM, provider registry, fallback `plan_only`,
  `agent` sem LLM, plugins e validacao estrita, sem chamar sistemas
  externos.
- `verify-release-alignment.mjs`: valida alinhamento de versao entre CLI,
  pacote npm, notas de release e contratos estruturais antes do corte.

Uso:

```bash
python3 scripts/validate-repo.py
python3 scripts/validate-repo.py --json
python3 scripts/validate-repo.py --strict
python3 scripts/mvp-readiness.py
python3 scripts/mvp-readiness.py --json
npm run release:verify -- v0.0.3
```

## Regras

- Nao coloque scripts especializados de dominio aqui.
- Integracoes executaveis de um agente devem ficar em
  `agents/<agent-id>/infra/integrations/<provider>/`.
- Runners de capabilities devem ficar na propria capability e ser declarados em
  `capability.yaml`.
- Se uma automacao nao atua sobre o repositorio inteiro, ela provavelmente nao
  pertence a esta pasta.
