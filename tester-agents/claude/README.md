# agex-tester (claude)

Culture-connected agent that dogfoods `agex` end-to-end from a Claude Code runtime and files findings back to the culture mesh.

## Register

```bash
culture agent register tester-agents/claude/
culture start <server>-agex-tester-claude
```

## What it tests

Per `CLAUDE.md`: one short bullet per command (`explain agex`, `overview`, `learn` menu, `learn introspect`, `gamify + hook read + gamify --uninstall`) reporting pass/fail, output length, and anything weird.

## Symlink note

`.claude/skills/` is a symlink to `../../../src/agent_experience/commands/` so the tester exercises the real shipped SKILL.md files rather than a stale copy. **On Windows, directory symlinks require Developer Mode or elevated privileges** — if `git clone` on Windows refuses to materialize the symlink, either enable Developer Mode (Settings → For developers) or clone with `git -c core.symlinks=true clone ...` from an elevated shell. The spec notes this as a known platform limitation.
