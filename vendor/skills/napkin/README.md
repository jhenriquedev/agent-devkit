# Napkin (instalação agnóstica de agente)

Skill que dá ao agente memória persistente dos próprios erros: um runbook
markdown por repositório, lido no início de cada sessão e atualizado
continuamente durante o trabalho. Ao longo das sessões, o agente para de repetir
erros já corrigidos e passa a antecipar problemas.

## Instalação neste DevKit

Diferente da instalação padrão (que fica em `.claude/skills/`), aqui o napkin é
**agnóstico de agente**:

- **Fonte única** em `skills/napkin/` (este diretório).
- **Ativação** declarada no `AGENTS.md` da raiz — padrão aberto lido por Claude
  Code, Codex, Cursor, Copilot, Gemini e outros.
- **Runbook** mantido em `skills/napkin/napkin.md` (caminho neutro, não atrelado
  a nenhum agente).

Não depende de auto-descoberta específica de ferramenta: qualquer agente que
leia o `AGENTS.md` passa a seguir o skill.

## Como funciona

1. **Início da sessão**: o agente lê `skills/napkin/napkin.md` (cria se não
   existir).
2. **Durante o trabalho**: registra gotchas, correções, preferências e o que
   funcionou — no momento em que acontecem.
3. **Ao longo das sessões**: o runbook é curado (re-priorizado, deduplicado,
   máx. 10 itens por categoria), virando uma base de conhecimento viva.

## Versionar ou não

O runbook em `skills/napkin/napkin.md` pode ser commitado (todos os
contribuidores e agentes se beneficiam do aprendizado) ou adicionado ao
`.gitignore` (mantém pessoal). Escolha do time.

---

> Fonte: https://github.com/blader/napkin (MIT). Adaptado para instalação
> agnóstica de agente neste repositório.
