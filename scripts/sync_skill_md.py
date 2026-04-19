"""Copy top-level command SKILL.md files into docs/commands/ for Jekyll rendering.

Each source file ships a YAML frontmatter block that `agex explain` and
`agex learn` know how to consume. Jekyll uses its own frontmatter schema
(title, layout, nav_order, parent), so this script parses the source
frontmatter with the in-repo SKILL.md loader, discards it, and prepends
a Jekyll-friendly frontmatter pointing at the `Commands` parent page.

Only iterates the five top-level command directories — lessons stay in
`agex learn` / `agex explain` territory for v0.1.
"""

from pathlib import Path

from agent_experience.core.skill_loader import load_skill

ROOT = Path(__file__).resolve().parent.parent
COMMANDS = ROOT / "src" / "agent_experience" / "commands"
DOCS_COMMANDS = ROOT / "docs" / "commands"

_JEKYLL_FRONTMATTER = (
    "---\n"
    "title: {title}\n"
    "layout: default\n"
    "parent: Commands\n"
    "nav_order: {order}\n"
    "---\n\n"
)

_INDEX_FRONTMATTER = (
    "---\n"
    "title: Commands\n"
    "layout: default\n"
    "nav_order: 3\n"
    "has_children: true\n"
    "---\n\n"
    "# Commands\n\n"
    "Auto-imported from `src/agent_experience/commands/*/SKILL.md` by"
    " `scripts/sync_skill_md.py`. Re-run the script after editing any"
    " command SKILL.md to refresh these pages.\n"
)


def _top_level_command_skill_md() -> list[Path]:
    """Return command SKILL.md paths in deterministic (alphabetical) order."""
    return sorted(
        cmd_dir / "SKILL.md"
        for cmd_dir in COMMANDS.iterdir()
        if cmd_dir.is_dir() and (cmd_dir / "SKILL.md").is_file()
    )


def main() -> int:
    DOCS_COMMANDS.mkdir(parents=True, exist_ok=True)
    for order, skill_md in enumerate(_top_level_command_skill_md(), start=1):
        skill = load_skill(skill_md)
        page = _JEKYLL_FRONTMATTER.format(title=skill.name, order=order * 10) + skill.body
        out_path = DOCS_COMMANDS / f"{skill_md.parent.name}.md"
        out_path.write_text(page, encoding="utf-8")
    (DOCS_COMMANDS / "index.md").write_text(_INDEX_FRONTMATTER, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
