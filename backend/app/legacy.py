"""Keep installs from before the rename working.

The app was called "Collander" through 1.x. Its settings used the ``COLLANDER_``
prefix and its database was ``collander.db``. Both still work: old settings are
copied to their new names unless the new name is already set, and the old
database file is renamed the first time the app starts.
"""

from __future__ import annotations

import logging
import os
from collections.abc import MutableMapping
from pathlib import Path

from dotenv import dotenv_values

PREFIX = "COLANDER_"
LEGACY_PREFIX = "COLLANDER_"
DB_NAME = "colander.db"
LEGACY_DB_NAME = "collander.db"

log = logging.getLogger(__name__)

# Settings read from their old names; logged once the app has set up logging.
adopted_env: list[str] = []


def adopt_legacy_env(
    env: MutableMapping[str, str] = os.environ, env_file: Path = Path(".env")
) -> list[str]:
    """Copy ``COLLANDER_*`` settings to ``COLANDER_*`` where the new name isn't set.

    Looks at the environment and, like the settings loader, a ``.env`` file in the
    working directory. Returns the old names that were used.
    """
    from_file = {k: v for k, v in dotenv_values(env_file).items() if v is not None}
    have = set(env) | set(from_file)
    used = []
    # The environment wins over .env, as it does for the new names.
    for key, value in {**from_file, **env}.items():
        if key.startswith(LEGACY_PREFIX):
            new = PREFIX + key[len(LEGACY_PREFIX) :]
            if new not in have:
                env[new] = value
                used.append(key)
    adopted_env[:] = used
    return used


def adopt_legacy_db(data_dir: Path) -> bool:
    """Rename ``collander.db`` (and its WAL files) to ``colander.db`` if only the old one exists."""
    old, new = data_dir / LEGACY_DB_NAME, data_dir / DB_NAME
    if new.exists() or not old.exists():
        return False
    # Sidecars first: if this is interrupted, the main file still has its old name
    # and the next start finishes the job.
    for suffix in ("-wal", "-shm"):
        side = data_dir / (LEGACY_DB_NAME + suffix)
        if side.exists():
            side.rename(data_dir / (DB_NAME + suffix))
    old.rename(new)
    log.info("Renamed %s to %s", old, new)
    return True


def log_adopted_env() -> None:
    if adopted_env:
        log.warning(
            "Using old setting names %s. They still work, but rename them to start with %s.",
            ", ".join(adopted_env),
            PREFIX,
        )
