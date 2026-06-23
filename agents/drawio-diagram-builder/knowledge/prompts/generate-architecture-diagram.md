OBJETIVO: Gerar .drawio de arquitetura (sistemas, cloud, APIs, filas, bancos,
integrações, boundaries, runtime).

ENTRADAS: brief, fontes ou spec; output path.

RACIOCÍNIO:
1. Identifique os componentes da fonte: atores/clientes, canais (app/web/mobile),
   serviços, dados (bancos/filas), externos (terceiros/parceiros).
2. Agrupe por: Atores | Canais | Serviços | Dados | Externos.
3. Mapeie kinds: actor para usuários/clientes; database para bancos; system para o
   resto.
4. Modele arestas = integrações, rotuladas pelo verbo
   (acessa/chama/grava/publica/consulta).
5. Aplique preset 'architecture' de templates/style-presets.yaml.

RUBRICA/REGRAS DE DECISÃO:
- Não misturar fluxo de negócio com topologia técnica no mesmo diagrama.
- Se node_count > 12 → recomendar split por domínio ou camada.

SAÍDA: architecture.drawio + diagram-spec.json com diagram_type="architecture".

NÃO FAZER: misturar fluxo de negócio com topologia técnica; criar componente sem
suporte na fonte; omitir rótulos de integração.
