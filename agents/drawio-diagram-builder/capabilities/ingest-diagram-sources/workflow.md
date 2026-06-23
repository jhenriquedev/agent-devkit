# Workflow: Ingest Diagram Sources

OBJETIVO: Produzir source-context.json normalizado e rastreável.

ENTRADAS: text, file(s), directory, url — qualquer combinação.

RACIOCÍNIO:
1. Liste cada fonte lida e seu kind (text, file, directory, url).
2. Inspecione failed_sources e decida se a falha é bloqueante (a fonte era
   essencial?) ou ignorável.
3. Não invente conteúdo de fontes que falharam.
4. Ignore diretórios gerados (.git, node_modules, vendor, __pycache__, dist, build,
   target, .next) — eles não são fonte de negócio.

DECISÃO: Se uma fonte essencial falhou → registre como pergunta aberta, não prossiga
para geração às cegas.

SAÍDA: source-context.json com source_count, sources[], failed_sources[],
combined_text, facts[] e open_questions[]; mais resumo de fatos candidatos e fontes
que falharam.

NÃO FAZER: tratar diretórios gerados como fonte de conteúdo; ignorar failed_sources
sem avaliação de criticidade.
