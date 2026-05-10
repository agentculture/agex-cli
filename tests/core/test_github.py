import subprocess

import pytest
import yaml

from agent_experience.core import github


class _FakeCompleted:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_run_gh_returns_stdout(monkeypatch):
    captured = {}

    def fake_run(cmd, capture_output, text, check, env=None):
        captured["cmd"] = cmd
        return _FakeCompleted(stdout='{"foo":1}', returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    out = github._run_gh(["api", "/foo"])
    assert out == '{"foo":1}'
    assert captured["cmd"][:2] == ["gh", "api"]


def test_run_gh_raises_runtimeerror_on_failure(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: _FakeCompleted(stderr="boom\nextra", returncode=1),
    )
    with pytest.raises(RuntimeError, match="gh failed: boom"):
        github._run_gh(["api", "/foo"])


def test_resolve_nick_from_culture_yaml(tmp_path):
    (tmp_path / "culture.yaml").write_text(
        yaml.safe_dump({"agents": [{"name": "a", "suffix": "my-nick"}]})
    )
    assert github.resolve_nick(tmp_path) == "my-nick"


def test_resolve_nick_falls_back_to_repo_basename(tmp_path):
    project = tmp_path / "agex-cli"
    project.mkdir()
    assert github.resolve_nick(project) == "agex-cli"


def test_resolve_nick_culture_yaml_without_suffix(tmp_path):
    project = tmp_path / "agex-cli"
    project.mkdir()
    (project / "culture.yaml").write_text(yaml.safe_dump({"agents": [{"name": "a"}]}))
    assert github.resolve_nick(project) == "agex-cli"
