# Decision Rules: Extract Log Samples

- Samples must be bounded.
- Do not reproduce visible segredo, token, API key or `Authorization` header values.
- If a payload appears sensitive, signal the field and redact the value.
- Keep event IDs when available.
- Preserve enough context for investigation without dumping raw payloads.
