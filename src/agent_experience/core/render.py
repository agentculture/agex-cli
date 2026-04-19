from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

# We render markdown for agent / CLI consumption — never HTML in a browser.
# select_autoescape([]) makes the intent explicit: escape nothing, for any
# extension. Enabling auto-escape here would corrupt markdown output.
_ENV = Environment(
    loader=FileSystemLoader("."),
    autoescape=select_autoescape([]),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)


# S5496 is suppressed inline (NOSONAR) below and also documented in
# sonar-project.properties. Rationale: render_string() renders Jinja
# templates that are always package-shipped (never user-controlled), and
# the output is markdown consumed by LLMs / the terminal — never rendered
# in an HTML context. Auto-escape is disabled deliberately (see
# select_autoescape([]) above). SonarCloud Automatic Analysis does not
# honor the project-properties suppression, so the NOSONAR tag is the
# load-bearing one; keeping both keeps a manual CLI scanner happy too.
def render_string(template: str, context: dict[str, Any]) -> str:
    return _ENV.from_string(template).render(**context)  # NOSONAR(pythonsecurity:S5496)


def render_file(path: Path, context: dict[str, Any]) -> str:
    return render_string(path.read_text(), context)
