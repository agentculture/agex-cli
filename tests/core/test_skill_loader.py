import pytest

from agent_experience.core.skill_loader import Skill, load_skill


def test_load_skill_parses_frontmatter_and_body(tmp_path):
    path = tmp_path / "SKILL.md"
    path.write_text(
        "---\n"
        "name: overview\n"
        "description: Snapshot of agent setup.\n"
        "type: command\n"
        "---\n"
        "\n"
        "# Overview body\n"
    )
    skill = load_skill(path)
    assert skill.name == "overview"
    assert skill.description == "Snapshot of agent setup."
    assert skill.type == "command"
    assert "# Overview body" in skill.body


def test_load_skill_missing_frontmatter_raises(tmp_path):
    path = tmp_path / "SKILL.md"
    path.write_text("# No frontmatter\n")
    with pytest.raises(ValueError) as exc:
        load_skill(path)
    assert "frontmatter" in str(exc.value).lower()


def test_load_skill_missing_required_field_raises(tmp_path):
    path = tmp_path / "SKILL.md"
    path.write_text("---\nname: x\n---\nbody\n")
    with pytest.raises(ValueError) as exc:
        load_skill(path)
    assert "description" in str(exc.value)
