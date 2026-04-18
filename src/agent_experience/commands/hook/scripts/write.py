from datetime import datetime, timezone

from agent_experience.core.hook_io import append_event
from agent_experience.core.paths import ensure_init


def run(event: str, args: list[str]) -> tuple[str, int, str]:
    ensure_init()
    payload: dict = {"ts": datetime.now(tz=timezone.utc).isoformat()}
    for arg in args:
        if "=" in arg:
            k, v = arg.split("=", 1)
            if k:
                payload[k] = v
    # Positional event name is authoritative — it overrides any `event=...`
    # pair in args so hook scripts can't misattribute events.
    payload["event"] = event
    append_event(event, payload)
    return ("", 0, "")
