# Prompt: Identify Missing Information

## OBJETIVO
Listar o que falta para gerar artefatos executáveis ou rodar testes de integração.

## ENTRADAS
- Mesmas flags de origem (`--url`, `--file`, `--directory`, `--text`)
- `--output` (opcional)

## RACIOCÍNIO
1. Compare o contrato extraído com os requisitos de execução e geração de artefato.
2. Agrupe lacunas por categoria: ambiente, autenticação, operações, dados, segurança.
3. Ordene primeiro as lacunas que BLOQUEIAM mutations reais.

## RUBRICA / REGRAS DE DECISÃO
- Sem base URL + há operações → perguntar base URL sandbox/homologação.
- Sem auth → perguntar mecanismo e variáveis de credencial.
- Há mutation → perguntar ambiente seguro e critério de cleanup.
- Sem operações → perguntar quais endpoints/comandos compõem a integração.

## SAÍDA
Markdown seguindo `identify-missing-information-output.md`:
seção "Perguntas" agrupadas por categoria, ordenadas por gravidade bloqueante.

## NÃO FAÇA
- Pedir segredo bruto quando variável de ambiente ou placeholder resolve o problema.
- Repetir perguntas que já estão respondidas na documentação fonte.
