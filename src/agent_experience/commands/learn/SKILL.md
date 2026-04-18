---
name: learn
description: Show available lessons, or teach one.
type: command
---

# `agex learn [topic] --agent <backend>`

Without a topic, lists the lessons available for your backend. With a topic, teaches it — emits a markdown lesson body plus inline skill-template code blocks you can write into your project.

## From your shell tool

```bash
agex learn --agent claude-code
agex learn introspect --agent claude-code
```

## Notes

- Lessons gated on a backend feature (e.g., `gamify` needs hooks) are still listed, marked with an unsupported note.
- v0.1 emits inline code blocks only. A future `--write` flag is tracked as an open issue.
