# generate-template-input-file

OBJETIVO: Gerar o arquivo de entrada (input-schema) para uma versão de
template, permitindo ao usuário saber quais dados fornecer.

ENTRADAS: --template-id (obrigatório); --template-version; --templates-root;
--output.

RACIOCÍNIO:
1. Resolva a versão do template (current_version se não especificada).
2. Inspecione o template.xlsx para extrair colunas esperadas por aba.
3. Gere input-schema.xlsx e input-schema.md com: nome da coluna, tipo esperado,
   obrigatoriedade e notas.
4. Se o input-schema já existe para a versão, exiba-o sem regenerar.

REGRAS DE DECISÃO:
- Se a versão não existe, falhe com erro claro.
- Input-schema deve refletir o sheet-map da versão, não inventar campos.

SAÍDA: input-schema.xlsx + input-schema.md na pasta da versão ou em --output.

NÃO FAZER: não modificar o template; não inventar colunas ausentes no template.
