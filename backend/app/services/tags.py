"""Tag normalization and lookup."""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from ..models import Tag


def normalize_tag(name: str) -> str:
    """Lowercase, trim, collapse whitespace/underscores into hyphens."""
    n = (name or "").strip().lower().lstrip("#")
    n = re.sub(r"[\s_]+", "-", n)
    n = re.sub(r"[^\w\-&'+]", "", n)
    n = re.sub(r"-{2,}", "-", n).strip("-")
    return n[:100]


def all_tag_names(db: Session) -> list[str]:
    return list(db.scalars(select(Tag.name).order_by(Tag.name)))


def get_or_create_tags(db: Session, names: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    seen: set[str] = set()
    for raw in names:
        name = normalize_tag(raw)
        if not name or name in seen:
            continue
        seen.add(name)
        tag = db.scalar(select(Tag).where(Tag.name == name))
        if tag is None:
            # Another queue worker may be adding the same new tag right now: insert unless
            # it exists by then, and read back whichever row won.
            db.execute(sqlite_insert(Tag).values(name=name).on_conflict_do_nothing())
            tag = db.scalar(select(Tag).where(Tag.name == name))
        tags.append(tag)
    return tags
