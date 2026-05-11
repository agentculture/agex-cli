---
name: cicd
description: How to use `agex pr` to ship a PR end-to-end — lint, open with auto-signature, fetch the unified briefing (status + comments + readiness), batch-reply with thread resolution, and run alignment-delta when needed.
type: lesson
---

# Lesson — CI/CD with `agex pr` for {{ backend }}

The full PR loop boils down to five commands. Each one ends with a
**Next step:** footer that names the right next command — chain it.

## Standard happy path

```bash
git checkout -b feat/<desc>
# ... edit ...
agex pr lint --agent {{ backend }}            # portability + alignment
git commit -am "..." && git push -u origin <branch>

agex pr open --agent {{ backend }} \
    --title "..." --body-file ./body.md \
    --delayed-read                          # creates PR + waits 180s + briefing

# briefing arrived; triage and prepare replies.jsonl, then:
agex pr reply <PR> --agent {{ backend }} < replies.jsonl

# fix anything, push, then:
agex pr read <PR> --agent {{ backend }} --wait 180
# repeat until reviewers quiet + CI green
# wait for human merge — never merge yourself
```

## When CLAUDE.md / culture.yaml / .claude/skills change

`agex pr lint` flags this and points you at:

```bash
agex pr delta --agent {{ backend }}
```

Read each sibling's CLAUDE.md head + culture.yaml, decide whether each
needs a follow-up PR, and mention any drift in your reply.

## JSONL reply shape

Each line of stdin to `agex pr reply <PR>`:

```json
{"in_reply_to": 123456, "thread_id": "T_kw...", "body": "Fixed in <commit>."}
```

- `in_reply_to` is the inline review-comment id. Omit for top-level conversation comments.
- `thread_id` triggers `resolveReviewThread` after the post.
- `body` is auto-signed with `- <nick> (Claude)` if the signature is missing. `<nick>` comes from the first agent's `suffix` in `culture.yaml`, falling back to the repo basename.

## Side effects

Network: every command except `lint` and `delta` talks to GitHub via `gh`.
Disk: `pr open`, `pr read`, and `pr reply` append events to
`.agex/data/pr/events.jsonl` for retrospective tooling.

## When something goes wrong

- `gh` not installed → `agex: install gh — https://cli.github.com/ — then rerun`
- `gh` not authenticated → `agex: run 'gh auth login' then rerun`
- `pr reply` partial failure → stderr names the line slice to resubmit; the
  command stops at the first failure to keep recovery surgical.
- `pr read --wait` timeout → exit 0 with a "Still waiting on: <reviewers>"
  banner; rerun the same command to keep waiting.

## Reply etiquette

Every comment gets a reply — no silent fixes. Always include a
`thread_id` so the thread closes automatically. Reference the fix-up
commit SHA in the reply body where relevant.
