from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///db.sqlite3"
engine = create_engine(DATABASE_URL, echo=False)


def init() -> None:
    SQLModel.metadata.create_all(engine)


def session_generator() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@contextmanager
def scoped_session() -> Generator[Session, None, None]:
    gen = session_generator()
    session = next(gen)
    try:
        yield session
    finally:
        gen.close()
