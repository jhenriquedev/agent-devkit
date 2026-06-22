# Decision Rules: Trace Request

- `identifier` e obrigatorio quando nao houver `fixture`.
- Preferir request id, correlation id, trace id ou hash tecnico como identificador.
- Nao usar PII, segredo, token, CPF, e-mail completo ou payload bruto; mascarar quando aparecer na saida.
- Ordenar timeline por timestamp e destacar eventos de erro.
- Informar quando nenhum evento for encontrado sem concluir que o request nao existiu.
- Manter janela restrita e citar lacunas sobre outros log groups ou sistemas.
