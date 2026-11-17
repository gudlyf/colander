import os
import subprocess
from functools import cache
from pathlib import Path

from .legacy import adopt_legacy_env

__version__ = "1.1.2"

# Before anything reads settings, so old COLLANDER_* names keep working everywhere.
adopt_legacy_env()


@cache
def commit() -> str | None:
    """The git commit this build came from.

    Release images bake it in as COLANDER_COMMIT; a source checkout asks git.
    """
    sha = os.environ.get("COLANDER_COMMIT", "").strip()
    if sha:
        return sha
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None
