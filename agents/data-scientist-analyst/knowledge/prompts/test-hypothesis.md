# test-hypothesis

## Objetivo
Executar teste de hipotese (diferenca de medias) e reportar decisao estatistica
unindo p-valor, effect size e relevancia pratica — nunca isolados.

## Entradas
- `--source` (obrigatorio).
- `--test-type mean-difference` (default).
- `--group-column` (obrigatorio): coluna que define os grupos.
- `--group-a`, `--group-b`: valores dos grupos a comparar.
- `--metric-column` (obrigatorio): metrica numerica.
- `--alpha`: nivel de significancia (default 0.05).

## Raciocinio
1. Confirme sha256, warnings, n por grupo.
2. Verifique assumptions: aproximacao normal (n >= 30 por grupo) e
   validity_warnings retornados.
3. Execute teste; obtenha p-valor, Cohen's d, IC da diferenca.
4. Decisao: rejeita H0 se p < alpha; qualifique com effect size e n.
5. Sempre reporte p E d E leitura pratica juntos — nunca p isolado.

## Rubrica de decisao
- p < alpha com d pequeno (< 0.2) -> "significante, porem efeito pequeno".
- n < 30 por grupo -> resultado fragil; declare assumptions violadas.
- validity_warnings presente -> bloqueie conclusao forte; aponte a limitacao.
- Rejeitar H0 nao implica causalidade — declare sempre.

## Saida
Decisao (rejeita/nao rejeita H0), p-valor, alpha, Cohen's d, IC da diferenca,
n por grupo, leitura executiva, limitacoes, bloco de rastreabilidade.

## Nao fazer
- Nao reportar p-valor sem effect size.
- Nao concluir causalidade com base em significancia.
- Nao ignorar validity_warnings.
