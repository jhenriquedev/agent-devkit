# Regras

- Usar serie agregada e z-score simples conforme metodo baseline do agente.
- Declarar threshold, granularidade e janela analisada.
- Tratar anomalia como sinal estatistico, nao como incidente confirmado.
- Sinalizar series curtas, baixa variancia ou sazonalidade nao modelada como limitacao.
- Nao remover anomalias da fonte.
- Mascarar detalhes sensiveis em amostras de periodos anomalos.
