from pathlib import Path

GITIGNORE_CONTENT = "# Managed by agex — do not edit.\ndata/\n"


def agex_dir(cwd: Path | None = None) -> Path:
    base = cwd if cwd is not None else Path.cwd()
    return base / ".agex"


def config_path(cwd: Path | None = None) -> Path:
    return agex_dir(cwd) / "config.toml"


def data_dir(cwd: Path | None = None) -> Path:
    return agex_dir(cwd) / "data"


def ensure_init(cwd: Path | None = None) -> Path:
    root = agex_dir(cwd)
    root.mkdir(parents=True, exist_ok=True)
    data_dir(cwd).mkdir(exist_ok=True)
    gi = root / ".gitignore"
    if not gi.exists():
        gi.write_text(GITIGNORE_CONTENT)
    return root
