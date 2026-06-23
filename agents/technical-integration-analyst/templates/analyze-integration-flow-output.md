# Fluxo de Uso da Integracao

## Ordem recomendada

1. Configurar autenticacao e obter token/credencial valida.
2. Executar {METHOD} {/setup_path}.
3. Executar {METHOD} {/read_path}.
4. Executar {METHOD} {/mutation_path} (mutation).
5. Validar efeitos colaterais e executar cleanup quando aplicavel.

<!-- Passos numerados em ordem: auth → criacao → leitura → atualizacao → destrutivas → validacao → cleanup.
     Sufixo "(mutation)" para operacoes que modificam estado.
     IDs dinamicos encadeados usam placeholders: {{resource_id}}, {{token}}, etc. -->
