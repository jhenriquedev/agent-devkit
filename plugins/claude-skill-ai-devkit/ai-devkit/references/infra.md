# Infra

For infrastructure work:

1. Separate analysis from mutation.
2. Prefer read-only discovery for architecture, security, and observability.
3. For operations, generate a plan first and require explicit confirmation for
   execution.
4. For destructive or high-impact actions, require blast radius, target,
   rollback path, and confirmation.

If local runtime is available, use `agent run` and preserve guardrail results.
