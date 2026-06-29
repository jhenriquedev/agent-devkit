# Context

Selenium deve ser escolhido quando existe requisito WebDriver, Selenium Grid,
browser remoto corporativo, projeto legado, extensoes de browser ou padrao de
equipe ja estabelecido.

Playwright continua sendo preferencia para automacao web moderna quando nao ha
necessidade de WebDriver.

Classificacao de side effects:

- `read-only`: navegacao, leitura e captura sem alterar estado.
- `form-submit`: envio de formulario ou clique de salvamento.
- `external-write`: alteracao em sistema externo.
- `destructive`: exclusao, compra, cancelamento ou acao irreversivel.
