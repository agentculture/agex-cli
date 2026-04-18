"""Meta-tests that guard SKILL.md consistency across all commands and lessons.

These tests parametrize over every SKILL.md discovered under the commands
package and assert that frontmatter is valid.  They also verify that the
five top-level command SKILL.md files exist so that future renames or
deletions don't silently break the contract.

Note on resource loading: `as_file` is used (not `Path(str(files(...)))`)
because the Traversable pattern is the only approach that is safe across
zipapp/PEX and editable installs.  In CI and dev we install in editable
mode, so the returned Path objects remain valid after the `with` block
exits — but we capture them as `Path(p)` copies just to be explicit.
"""

from importlib.resources import as_file, files
from pathlib import Path

import pytest

from agent_experience.core.skill_loader import load_skill

_VALID_TYPES = frozenset({"command", "lesson"})


def _all_skill_md_paths() -> list[Path]:
    # Works because our package is installed in editable mode (hatch
    # force-include keeps SKILL.md on the filesystem, not inside a zip loader).
    with as_file(files("agent_experience.commands")) as root:
        return sorted(Path(p) for p in root.glob("**/SKILL.md"))


# ---------------------------------------------------------------------------
# Guard: ensure the parametrize fixture actually discovers enough files.
# If the import mechanics break, all parametrized tests silently pass (0
# items), so we add an explicit lower-bound check here.
# ---------------------------------------------------------------------------

def test_meta_test_discovers_all_known_skills() -> None:
    """Verify that at least 9 SKILL.md files are found (5 commands + 4 lessons)."""
    paths = _all_skill_md_paths()
    assert len(paths) >= 9, (
        f"Expected >= 9 SKILL.md files under agent_experience.commands, "
        f"found {len(paths)}: {[str(p) for p in paths]}"
    )


# ---------------------------------------------------------------------------
# Parametrized frontmatter tests — one test case per SKILL.md file.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "skill_path",
    _all_skill_md_paths(),
    ids=lambda p: "/".join(p.parts[p.parts.index("commands"):]),
)
def test_skill_md_has_valid_frontmatter(skill_path: Path) -> None:
    """Each SKILL.md must parse without error and have name, description, and type."""
    skill = load_skill(skill_path)
    assert skill.name, f"{skill_path}: 'name' frontmatter field is empty"
    assert skill.description, f"{skill_path}: 'description' frontmatter field is empty"
    assert skill.type in _VALID_TYPES, (
        f"{skill_path}: 'type' value {skill.type!r} is not one of {sorted(_VALID_TYPES)}"
    )


# ---------------------------------------------------------------------------
# Structural test — every top-level command must have a SKILL.md.
# ---------------------------------------------------------------------------

def test_every_command_has_skill_md() -> None:
    """Each of the five top-level commands must ship a SKILL.md."""
    with as_file(files("agent_experience.commands")) as commands_root:
        for cmd in ("explain", "overview", "learn", "gamify", "hook"):
            assert (commands_root / cmd / "SKILL.md").is_file(), (
                f"{cmd}/SKILL.md is missing from agent_experience.commands"
            )
