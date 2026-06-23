# UX Patterns — Regras de decisao por plataforma

## Classificacao de escopo
- **Tela:** uma view/screen isolada com objetivo unico.
- **Fluxo:** sequencia de 2–7 telas com um objetivo transacional (ex.: checkout).
- **Modulo:** conjunto de fluxos relacionados (ex.: modulo de usuarios).
- **Produto:** todos os modulos; implica design system completo.

## Padroes web responsivo

### Layout e hierarquia
- Hierarquia visual: tamanho tipografico > peso > cor > espacamento.
- Coluna unica em mobile (<640px), 12 colunas em desktop (>=1280px), 8 colunas em tablet.
- Margem lateral minima: 16px mobile, 24px tablet, auto (max-width 1280px) desktop.
- Grupos de conteudo separados por espacamento (nao linhas divisorias) sempre que possivel.

### Navegacao
- Navbar horizontal fixa para desktop/tablet; hamburguer ou bottom-nav para mobile.
- Breadcrumbs em paginas de detalhe com hierarquia >= 2 niveis.
- Botao de acao primario nunca oculto em scroll; use sticky footer em formularios longos.

### Breakpoints obrigatorios por tela criada
- mobile: 375px (ou 390px iPhone 14)
- tablet: 768px
- desktop: 1440px

## Padroes mobile (iOS/Material)

### iOS (SwiftUI/UIKit)
- Navegacao: TabBar para 2–5 destinos principais; NavigationStack para hierarquia.
- Frame padrao: iPhone 14 (390x844); iPhone SE (375x667).
- Safe area: respeitar top/bottom safe area insets em todos os frames.
- Tamanho minimo de alvo de toque: 44x44pt.

### Material (Android)
- Navegacao: NavigationBar na base para 3–5 destinos; NavigationDrawer para estruturas largas.
- Frame padrao: Pixel 7 (412x915dp).
- Tamanho minimo de alvo de toque: 48x48dp.

## Estados obrigatorios por tipo de tela

| Tipo de tela        | Estados obrigatorios                                  |
|---------------------|------------------------------------------------------|
| Listagem/feed       | loading, empty, populado, erro de rede               |
| Formulario          | idle, validando, erro de campo, enviando, sucesso     |
| Detalhe/visualizacao| loading, carregado, erro (404/sem permissao)         |
| Dashboard           | loading, dados presentes, sem dados, erro            |
| Autenticacao        | idle, digitando, erro de credencial, sucesso/redirect|
| Configuracoes       | carregado, salvo, erro ao salvar                     |
| Tela de erro        | 404, 500, sem conexao, sem permissao                 |

## Principios de design system

1. **Hierarquia de reuso:** token → componente primitivo → componente composto → template.
2. Sem design system existente: crie tokens minimos (cor primaria/secundaria/neutral/feedback, tipografia base, spacing scale 4px, border-radius).
3. Nomenclatura de tokens: `{categoria}/{escala}` ex.: `color/primary/500`, `spacing/4`.
4. Variantes de componente: padrao, hover, focus, disabled, loading (onde aplicavel).

## Acessibilidade basica (ver accessibility-rules.md para criterios completos)
- Contraste minimo: 4.5:1 para texto normal; 3:1 para texto grande (>=18pt regular ou >=14pt bold).
- Todo elemento interativo tem label textual visivel ou aria-label equivalente.
- Foco visivel em todos os elementos interativos (outline de 2px ou equivalente).
