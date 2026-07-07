import os
import tempfile

_tmp_dir = tempfile.mkdtemp(prefix="sentinel_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_dir}/test.db"
os.environ["CHROMA_PATH"] = os.path.join(_tmp_dir, "chroma")

import pytest  # noqa: E402

from app.db.base import Base, SessionLocal, engine  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
