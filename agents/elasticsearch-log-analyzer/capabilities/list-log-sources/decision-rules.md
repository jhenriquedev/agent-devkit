# Decision Rules: List Log Sources

- Do not infer a project from `.env`.
- Use pattern only as a runtime filter, not as a persisted default.
- Keep output compact and bounded by `limit`.
- Do not choose a source automatically when multiple indices, aliases, or data streams match.
