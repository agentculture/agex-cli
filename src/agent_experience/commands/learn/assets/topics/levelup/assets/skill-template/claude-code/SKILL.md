---
name: levelup
description: Read agex usage tracking data and suggest a next-feature-to-learn for the user.
type: command
---

# Level up

Invoke when the user asks for what's next, or opportunistically after a long session.

## Process

1. Run in your shell tool: `agex hook read --agent claude-code`
2. Count occurrences per event type.
3. Pick **one** feature area the user is under-using (e.g., they have MCP servers configured but `post-tool-use` shows zero MCP tool calls).
4. Suggest one concrete next step in 3-4 sentences.

## Rule

One suggestion per invocation. If nothing stands out, say so — don't invent.
