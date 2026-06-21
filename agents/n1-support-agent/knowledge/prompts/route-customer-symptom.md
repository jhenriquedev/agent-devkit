# Prompt

Classifique o sintoma do cliente usando o roteamento MeuCashCard.

## Regras

- Use o texto do card apenas como sinal de roteamento.
- Nao conclua causa raiz nesta etapa.
- Retorne checks minimos e regras de negocio que devem orientar o diagnostico.
- Quando nao houver rota clara, use rota `unknown` e registre lacuna objetiva.
