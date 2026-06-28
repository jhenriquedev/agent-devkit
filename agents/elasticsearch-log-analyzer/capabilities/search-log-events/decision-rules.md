# Decision Rules: Search Log Events

- Require explicit `source`, `from` and `to` for real calls; never search without a bounded janela.
- Never return unbounded events; respect `limit` and the repository max of 1000.
- Prefer structured filters over broad text queries when available.
- Do not print API keys or `Authorization` headers in output or errors.
