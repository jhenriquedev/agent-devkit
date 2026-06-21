# Metodos De Analise

O agente prioriza metodos simples, auditaveis e reproduziveis:

- inferencia de tipos por maioria de valores;
- perfil de colunas com nulos, unicos, frequencias e estatisticas numericas;
- deteccao de duplicidades por assinatura completa da linha;
- conciliacao por chave simples ou composta;
- tolerancia numerica configuravel;
- normalizacao de CPF/CNPJ para comparacao de chaves;
- score de qualidade baseado em completude e duplicidade.
- outliers por IQR e z-score;
- correlacao linear de Pearson entre variaveis numericas;
- segmentacao categorica com contagem, percentual e metricas agregadas;
- hipoteses exploratorias com declaracao explicita de limitacoes.
- series temporais agregadas por dia, semana ou mes;
- comparacao de periodos por delta absoluto e percentual;
- cohorts por data de entrada e idade em dias;
- anomalias temporais por z-score;
- forecast baseline por media movel.
