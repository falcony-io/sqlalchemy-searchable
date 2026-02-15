import os

import pytest
from sqlalchemy import (
    Column,
    create_engine,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import (
    close_all_sessions,
    configure_mappers,
    declarative_base,
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
def engine():
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
def session(engine):
    Session = sessionmaker(engine)
    session = Session()

    yield session

    session.expunge_all()
    close_all_sessions()


@pytest.fixture
def search_manager_regconfig():
    return None


@pytest.fixture
def Base(search_manager_regconfig):
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
def search_trigger_name():
    return "{table}_{column}_trigger"


@pytest.fixture
def search_trigger_function_name():
    return "{table}_{column}_update"


@pytest.fixture
def search_options(search_trigger_name, search_trigger_function_name):
    return SearchOptions(
        search_trigger_name=search_trigger_name,
        search_trigger_function_name=search_trigger_function_name,
        auto_index=True,
    )


@pytest.fixture(autouse=True)
def create_tables(Base, engine, models):
    configure_mappers()
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def models(TextItem, Article):
    pass


@pytest.fixture
def TextItem(
    Base,
    search_trigger_function_name,
    search_trigger_name,
):
    ts_vector_options = {
        "auto_index": True,
        "search_trigger_name": search_trigger_name,
        "search_trigger_function_name": search_trigger_function_name,
    }

    class TextItem(Base):
        __tablename__ = "textitem"

        id = Column(Integer, primary_key=True, autoincrement=True)

        name = Column(String(255))

        search_vector = Column(TSVectorType("name", "content", **ts_vector_options))
        content_search_vector = Column(TSVectorType("content", **ts_vector_options))

        content = Column(Text)

    return TextItem


@pytest.fixture
def Article(TextItem):
    class Article(TextItem):
        __tablename__ = "article"
        id = Column(Integer, ForeignKey(TextItem.id), primary_key=True)
        created_at = Column(DateTime)

    return Article
