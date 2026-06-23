# Elasticsearch Log Report

## Scope

- Source: <source>
- From: <from>
- To: <to>
- Service: <service or ->
- Environment: <environment or ->
- Query: <query or ->

## Summary

<!-- Fatos -->
- Matching events: <total from count_events>
- Loaded samples: <count of events in this report>
- Limit reached: <true/false>

## Patterns

<!-- Inferência: fingerprints heurísticos -->
- <fingerprint>: <count>

## Samples

| Time | Service | Level | Trace | Message | ID |
|---|---|---|---|---|---|

## Next Steps

- Validate the highest-frequency patterns against recent deploys or infrastructure events.
- Narrow by service, environment, or trace ID if the result set is broad.

---
*Fatos: contagens e amostras do Elasticsearch. Padrões são inferências heurísticas.*
