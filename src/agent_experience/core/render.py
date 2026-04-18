from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_ENV = Environment(
    loader=FileSystemLoader("."),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)


def render_string(template: str, context: dict[str, Any]) -> str:
    return _ENV.from_string(template).render(**context)


def render_file(path: Path, context: dict[str, Any]) -> str:
    return render_string(path.read_text(), context)
