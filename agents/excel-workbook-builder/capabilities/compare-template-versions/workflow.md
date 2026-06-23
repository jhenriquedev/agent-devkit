# compare-template-versions

OBJETIVO: Comparar estrutura, schema e artefatos entre duas versões de
template para informar decisão de promoção ou descarte.

ENTRADAS: --template-id (obrigatório); --left-version; --right-version;
--templates-root; --output.

RACIOCÍNIO:
1. Carregue as duas versões do template.
2. Compare arquivos presentes em cada versão (adicionados/removidos).
3. Para cada .xlsx nas versões, use inspect-template para listar abas,
   fórmulas e validações e compare as diferenças.
4. Classifique diferenças por impacto (estrutural, de fórmula, de schema).
5. Produza relatório de comparação com recomendação.

REGRAS DE DECISÃO:
- Se alguma versão não existe, pare e reporte.
- Diferença estrutural (aba removida/renomeada) deve ser destacada como risco.

SAÍDA (markdown): seções Adicionados, Removidos, Modificados, Recomendação.

NÃO FAZER: não promover nem depreciar aqui; só comparar.
