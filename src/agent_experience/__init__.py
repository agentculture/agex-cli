from importlib.metadata import PackageNotFoundError, version

# `agex-cli` is the canonical PyPI distribution name; `agent-devex` is an
# alias distribution that ships the identical wheel under a different name.
# Whichever one is installed, surface its version. Falling through to a
# PEP 440 local-version sentinel keeps `agex --version` from crashing in
# unusual installs (e.g. running from an unbuilt source checkout).
for _dist in ("agex-cli", "agent-devex"):
    try:
        __version__ = version(_dist)
        break
    except PackageNotFoundError:
        continue
else:
    __version__ = "0.0.0+unknown"
