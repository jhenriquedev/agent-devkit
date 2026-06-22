# Analyze Code Root Cause

## Fluxo

1. Carregar contexto N2.
2. Validar `--codebase-path`.
3. Derivar tokens do sintoma e evidencias.
4. Percorrer arquivos de codigo suportados.
5. Ignorar diretorios de build/cache/vendor.
6. Pontuar caminho e conteudo por tokens.
7. Extrair assinaturas de metodos/classes.
8. Ordenar achados por prioridade de arquivo.

## Saida

Retorna arquivos, metodos e achados tecnicos candidatos.
