# Diagram Types

Supported families:

- Architecture: C4 context, C4 container, C4 component, cloud architecture,
  integration architecture, event-driven flow, deployment/runtime,
  observability, security boundaries.
- Product: user journey, service blueprint, onboarding, checkout, approval,
  conversion funnel, exception flow.
- Operations: runbook, incident, N1/N2 triage, escalation, support card state,
  decision tree.
- Data: ERD, lineage, ETL/ELT, reconciliation, domain relationships.

If source material mixes families, recommend a diagram package instead of one
overloaded page.

For ERD, extract entities/tables as nodes and relationships from `*_id` fields
or explicit phrases such as "pedido pertence a cliente". For architecture,
extract actors, channels, services, data stores, external systems, and labelled
actions between them.
