---
name: explain
description: Emit markdown documentation for any agex command, lesson, or concept.
type: command
---

# `agex explain <topic>`

Use this to get authoritative, deterministic documentation on an agex command, lesson, or concept without invoking a lesson or running a probe.

## How it resolves

1. `commands/<topic>/SKILL.md` (command-level, wins if present)
2. `commands/learn/assets/topics/<topic>/SKILL.md` (lesson-level)
3. `commands/explain/assets/topics/<topic>.md` (concept-level override)

First match wins.

## From your shell tool

```bash
agex explain overview
agex explain gamify
agex explain levelup
agex explain agex          # self-describing page
```
