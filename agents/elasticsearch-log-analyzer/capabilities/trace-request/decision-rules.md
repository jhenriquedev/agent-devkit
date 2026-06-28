# Decision Rules: Trace Request

- Do not assume a trace field; search common trace/correlation/request fields.
- Require explicit `source`, janela `from`/`to`, request identifier and `limit`.
- Keep the requested identificador visible in output without truncating it.
- If no events are found, recommend widening time window or source.
- Do not treat missing events as proof that the request never existed.
