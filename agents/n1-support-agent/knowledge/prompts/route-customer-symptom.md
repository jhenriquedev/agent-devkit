# Prompt

Classifique o sintoma do cliente usando o roteamento de suporte ao cliente.

## Regras

- Use o texto do card apenas como sinal de roteamento.
- Nao conclua causa raiz nesta etapa.
- Retorne checks minimos e regras de negocio que devem orientar o diagnostico.
- Quando nao houver rota clara, use rota `unknown` e registre lacuna objetiva.
