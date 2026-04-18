---
name: levelup
description: Build a skill that reads agex usage data and advises the user.
type: lesson
---

# Lesson — build the `levelup` skill for {{ backend }}

Prerequisite: you've run `agex gamify --agent {{ backend }}` so there's data to read.

## Step 1 — understand the data source

Run `agex hook read --agent {{ backend }}` now. You'll see a JSON list of events (tool calls, prompts submitted, stops). The levelup skill will parse this and suggest one area for improvement.

## Step 2 — create the skill file

Write the file shown below to the path noted above its fence. This skill reads the tracking data and offers one concrete suggestion per invocation.

### Skill template — `.claude/skills/levelup/SKILL.md`

```markdown
{{ skill_template_body }}
```

## Step 3 — try it after a few sessions

Use your runtime normally for a few turns. Then invoke `/levelup` to see what the skill suggests.

See also: `agex learn gamify --agent {{ backend }}` (bundles the full setup).
