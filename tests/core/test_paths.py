from agent_experience.core.paths import agex_dir, config_path, data_dir, ensure_init


def test_agex_dir_uses_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert agex_dir() == tmp_path / ".agex"


def test_ensure_init_creates_dir_and_gitignore(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ensure_init()
    assert (tmp_path / ".agex").is_dir()
    assert (tmp_path / ".agex" / "data").is_dir()
    gi = tmp_path / ".agex" / ".gitignore"
    assert gi.exists()
    assert "data/" in gi.read_text()


def test_ensure_init_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ensure_init()
    (tmp_path / ".agex" / "existing.txt").write_text("keep me")
    ensure_init()
    assert (tmp_path / ".agex" / "existing.txt").read_text() == "keep me"


def test_config_path_and_data_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ensure_init()
    assert config_path() == tmp_path / ".agex" / "config.toml"
    assert data_dir() == tmp_path / ".agex" / "data"
