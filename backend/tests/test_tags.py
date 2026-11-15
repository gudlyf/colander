import threading

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Tag
from app.schemas import RecipeIn
from app.services.recipes import create_recipe
from app.services.tags import get_or_create_tags


def _at_once(work, n=4) -> list[Exception]:
    """Run work(db, i) in n threads that start together, each with its own session."""
    barrier = threading.Barrier(n)
    errors: list[Exception] = []

    def run(i):
        db = SessionLocal()
        try:
            barrier.wait()
            work(db, i)
            db.commit()
        except Exception as e:  # noqa: BLE001
            errors.append(e)
        finally:
            db.close()

    threads = [threading.Thread(target=run, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return errors


def test_new_tag_created_by_two_imports_at_once(client):
    # Queue workers run in parallel and often add the same new tag at the same moment.
    for n in range(15):
        name = f"race-tag-{n}"

        def work(db, _i, name=name):
            assert [t.name for t in get_or_create_tags(db, [name])] == [name]

        errors = _at_once(work)
        assert not errors, errors[0]
        with SessionLocal() as db:
            assert db.scalar(select(func.count()).where(Tag.name == name)) == 1


def test_parallel_recipe_saves_share_a_new_tag(client):
    for n in range(10):
        name = f"shared-new-tag-{n}"

        def work(db, i, name=name):
            create_recipe(
                db, RecipeIn(title=f"{name} {i}", ingredients=[{"text": "1 egg"}], tags=[name])
            )

        errors = _at_once(work)
        assert not errors, errors[0]
        assert client.get("/api/recipes", params={"tag": name}).json()["total"] == 4
