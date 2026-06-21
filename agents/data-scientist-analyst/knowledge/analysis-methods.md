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
- teste de hipotese para diferenca de medias com aproximacao normal;
- intervalos de confianca para media;
- tamanho de amostra para duas proporcoes balanceadas;
- Cohen's d para tamanho de efeito;
- interpretacao de p-valor, alpha e relevancia pratica.
- preparo de dataset de modelagem com alvo, features e split deterministico;
- baseline de classificacao binaria por melhor threshold numerico;
- avaliacao por accuracy, precision, recall, F1 e matriz de confusao;
- deteccao heuristica de leakage por copia de alvo e nomes pos-evento;
- monitoramento baseline de drift por deslocamento de media normalizado.
