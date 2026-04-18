from pathlib import Path

from agent_experience.backends.codex.probe import probe as codex_probe
from agent_experience.backends.copilot.probe import probe as copilot_probe
from agent_experience.backends.acp.probe import probe as acp_probe


def test_codex_probe_empty_on_empty_project(tmp_path):
    assert codex_probe(tmp_path).skills == []


def test_codex_probe_reads_agents_md(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# AGENTS\n")
    result = codex_probe(tmp_path)
    assert result.claude_md is not None


def test_copilot_probe_empty(tmp_path):
    assert copilot_probe(tmp_path).skills == []


def test_acp_probe_empty(tmp_path):
    assert acp_probe(tmp_path).skills == []
