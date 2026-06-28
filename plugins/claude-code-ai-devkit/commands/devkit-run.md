# devkit-run

Run a deterministic capability:

```bash
python3 plugins/claude-code-ai-devkit/scripts/run-capability.py --json <agent> <capability> [args...]
```

If the result contains `status: partial`, preserve `fallback_applied`, risks,
and next steps in the response.
