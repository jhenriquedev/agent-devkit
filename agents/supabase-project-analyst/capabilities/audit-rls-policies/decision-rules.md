# Decision Rules

- `auth.role()` deve ser reportado.
- `TO authenticated` sem `auth.uid()`/ownership deve ser reportado.
- UPDATE sem `WITH CHECK` deve ser reportado.
- Nao aplicar policy.
