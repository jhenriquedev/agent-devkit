# Read Incident

## Objetivo

Ler um incidente TOPdesk por ID ou numero e, quando solicitado, carregar o
progress trail.

## Entradas

- `id` ou `number`.
- `include_progress_trail`.
- `fixture` para execucao offline.

## Raciocinio

1. Exija ID ou numero; nao adivinhe o incidente.
2. Leia o incidente pelo repository.
3. Carregue progress trail quando o usuario pedir historico ou quando uma escrita
   posterior depender de contexto.
4. Separe identificacao, solicitacao e historico.
5. Evite inferencias fora da evidencia carregada.

## Rubrica

- ID e numero sao fatos TOPdesk.
- Progress trail e historico, nao prova de causa raiz por si so.
- Se faltar informacao, aponte lacuna sem alterar o chamado.

## Saida

Bloco de identificacao, solicitacao e ate 20 entradas de progress trail.

## Nao faca

Nao expor payload raw. Nao concluir categoria ou prioridade. Nao executar escrita.
