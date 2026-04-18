---
name: hook
description: Write and read agex tracking events.
type: command
---

# `agex hook write <event> [key=value ...]` / `agex hook read --agent <backend>`

## `write`

Called by installed hooks (see `agex gamify`). Appends a JSON line to `.agex/data/<event>.json`. Silent. Safe for concurrent invocation.

```bash
agex hook write post-tool-use tool=Read
```

## `read`

Renders tracked events as a markdown table. Prints the source JSON path for deeper inspection.

```bash
agex hook read --agent claude-code
```

## Notes

- Event names are free-form; conventional names: `post-tool-use`, `user-prompt`, `stop`, `sessions`.
- Extra positional `key=value` pairs are captured into the payload.
- Timestamp is attached automatically if not supplied.
