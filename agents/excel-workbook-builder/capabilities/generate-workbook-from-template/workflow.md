# generate-workbook-from-template  (DEPENDE DO RUNTIME NODE)

OBJETIVO: Preencher a aba de dados de um template versionado com dados
normalizados, preservando todas as outras abas, fórmulas e layout.

ENTRADAS: --input (JSON normalizado obrigatório); --template-id (obrigatório);
--template-version (default: current_version); --output; --sheet (aba alvo,
default: Data).

RACIOCÍNIO:
1. PRÉ-CHECK do runtime Node (ver runtime.md).
2. Resolva a versão do template (current_version se não especificada).
3. Inspecione o template com inspect-template para confirmar aba alvo.
4. Execute map-source-to-template se mapping não fornecido.
5. Preencha somente a aba alvo; preserve o restante do template intacto.
6. Execute quality gates obrigatórios após gerar.

REGRAS DE DECISÃO:
- Aba alvo não encontrada no template: pause e pergunte ao usuário.
- Campos obrigatórios unmapped: pause antes de gerar.
- Nunca toque em abas fora da aba alvo.

SAÍDA: workbook.xlsx preenchido no caminho --output.

NÃO FAZER: não tocar abas fora da alvo; não gerar sem mapping validado.
