import os
from collections.abc import Generator
from datetime import datetime
from typing import Any

import pytest
from sqlalchemy import (
    create_engine,
    ForeignKey,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    close_all_sessions,
    configure_mappers,
    declarative_base,
    DeclarativeBase,
    Mapped,
    mapped_column,
    Session,
    sessionmaker,
)
from sqlalchemy_utils import TSVectorType

from sqlalchemy_searchable import (
    make_searchable,
    remove_listeners,
    search_manager,
    SearchOptions,
    vectorizer,
)

try:
    import __pypy__
except ImportError:
    __pypy__ = None


if __pypy__:
    from psycopg2cffi import compat

    compat.register()


@pytest.fixture
def engine() -> Generator[Engine, None, None]:
    db_user = os.environ.get("SQLALCHEMY_SEARCHABLE_TEST_USER", "postgres")
    db_password = os.environ.get("SQLALCHEMY_SEARCHABLE_TEST_PASSWORD", "")
    db_name = os.environ.get(
        "SQLALCHEMY_SEARCHABLE_TEST_DB", "sqlalchemy_searchable_test"
    )
    url = f"postgresql://{db_user}:{db_password}@localhost/{db_name}"

    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS hstore"))

    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Generator[Session, None, None]:
    SessionFactory = sessionmaker(engine)
    session = SessionFactory()

    yield session

    session.expunge_all()
    close_all_sessions()


@pytest.fixture
def search_manager_regconfig() -> None:
    return None


@pytest.fixture
def Base(
    search_manager_regconfig: str | None,
) -> Generator[type[DeclarativeBase], None, None]:
    Base = declarative_base()
    if search_manager_regconfig:
        make_searchable(
            Base.metadata,
            options=SearchOptions(regconfig=search_manager_regconfig),
        )
    else:
        make_searchable(Base.metadata)

    yield Base

    search_manager.processed_columns = []
    vectorizer.clear()
    remove_listeners(Base.metadata)


@pytest.fixture
def search_trigger_name() -> str:
    return "{table}_{column}_trigger"


@pytest.fixture
def search_trigger_function_name() -> str:
    return "{table}_{column}_update"


@pytest.fixture
def search_options(
    search_trigger_name: str,
    search_trigger_function_name: str,
) -> SearchOptions:
    return SearchOptions(
        search_trigger_name=search_trigger_name,
        search_trigger_function_name=search_trigger_function_name,
        auto_index=True,
    )


@pytest.fixture(autouse=True)
def create_tables(
    Base: type[DeclarativeBase],
    engine: Engine,
    models: None,
) -> Generator[None, None, None]:
    configure_mappers()
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def models(TextItem: type[Any], Article: type[Any]) -> None:
    pass


@pytest.fixture
def TextItem(
    Base: type[DeclarativeBase],
    search_trigger_function_name: str,
    search_trigger_name: str,
) -> type[Any]:
    ts_vector_options = {
        "auto_index": True,
        "search_trigger_name": search_trigger_name,
        "search_trigger_function_name": search_trigger_function_name,
    }

    class TextItem(Base):  # type: ignore[misc, valid-type]
        __tablename__ = "textitem"

        id: Mapped[int] = mapped_column(primary_key=True)

        name: Mapped[str]

        search_vector: Mapped[TSVectorType] = mapped_column(
            TSVectorType("name", "content", **ts_vector_options)
        )
        content_search_vector: Mapped[TSVectorType] = mapped_column(
            TSVectorType("content", **ts_vector_options)
        )

        content: Mapped[str]

    return TextItem


@pytest.fixture
def Article(TextItem: type[Any]) -> type[Any]:
    class Article(TextItem):  # type: ignore[misc]
        __tablename__ = "article"
        id: Mapped[int] = mapped_column(ForeignKey(TextItem.id), primary_key=True)
        created_at: Mapped[datetime | None]

    return Article
