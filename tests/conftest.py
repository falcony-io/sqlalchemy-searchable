import os

import pytest
from sqlalchemy import (
    Column,
    create_engine,
    DateTime,
    ForeignKey,
    Integer,
    text,
    Unicode,
    UnicodeText,
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
    vectorizer,
)

try:
    import __pypy__
except ImportError:
    __pypy__ = None


if __pypy__:
    from psycopg2cffi import compat

    compat.register()


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "postgresql_min_version(min_version): "
        "skip the test if PostgreSQL version is less than min_version",
    )
    config.addinivalue_line(
        "markers",
        "postgresql_max_version(max_version): "
        "skip the test if PostgreSQL version is greater than max_version",
    )


@pytest.fixture
def engine():
    db_user = os.environ.get("SQLALCHEMY_SEARCHABLE_TEST_USER", "postgres")
    db_password = os.environ.get("SQLALCHEMY_SEARCHABLE_TEST_PASSWORD", "")
    db_name = os.environ.get(
        "SQLALCHEMY_SEARCHABLE_TEST_DB", "sqlalchemy_searchable_test"
    )
    url = f"postgresql://{db_user}:{db_password}@localhost/{db_name}"

    engine = create_engine(url, future=True)
    engine.echo = True
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS hstore"))

    yield engine
    engine.dispose()


@pytest.fixture
def postgresql_version(engine):
    with engine.connect():
        major, _ = engine.dialect.server_version_info
        return major


@pytest.fixture(autouse=True)
def check_postgresql_min_version(request, postgresql_version):
    postgresql_min_version_mark = request.node.get_closest_marker(
        "postgresql_min_version"
    )
    if postgresql_min_version_mark:
        min_version = postgresql_min_version_mark.args[0]
        if postgresql_version < min_version:
            pytest.skip(f"Requires PostgreSQL >= {min_version}")


@pytest.fixture(autouse=True)
def check_postgresql_max_version(request, postgresql_version):
    postgresql_max_version_mark = request.node.get_closest_marker(
        "postgresql_max_version"
    )
    if postgresql_max_version_mark:
        max_version = postgresql_max_version_mark.args[0]
        if postgresql_version > max_version:
            pytest.skip(f"Requires PostgreSQL <= {max_version}")


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine, future=True)
    session = Session(future=True)

    yield session

    session.expunge_all()
    close_all_sessions()


@pytest.fixture
def search_manager_regconfig():
    return None


@pytest.fixture
def Base(search_manager_regconfig):
    Base = declarative_base()
    make_searchable(Base.metadata)
    if search_manager_regconfig:
        search_manager.options["regconfig"] = search_manager_regconfig

    yield Base

    search_manager.options["regconfig"] = "pg_catalog.english"
    search_manager.processed_columns = []
    vectorizer.clear()
    remove_listeners(Base.metadata)


@pytest.fixture
def remove_symbols():
    return "-@."


@pytest.fixture
def search_trigger_name():
    return "{table}_{column}_trigger"


@pytest.fixture
def search_trigger_function_name():
    return "{table}_{column}_update"


@pytest.fixture
def ts_vector_options(
    remove_symbols, search_trigger_name, search_trigger_function_name
):
    return {
        "remove_symbols": remove_symbols,
        "search_trigger_name": search_trigger_name,
        "search_trigger_function_name": search_trigger_function_name,
        "auto_index": True,
    }


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
def TextItem(Base, ts_vector_options):
    class TextItem(Base):
        __tablename__ = "textitem"

        id = Column(Integer, primary_key=True, autoincrement=True)

        name = Column(Unicode(255))

        search_vector = Column(TSVectorType("name", "content", **ts_vector_options))
        content_search_vector = Column(TSVectorType("content", **ts_vector_options))

        content = Column(UnicodeText)

    return TextItem


@pytest.fixture
def Article(TextItem):
    class Article(TextItem):
        __tablename__ = "article"
        id = Column(Integer, ForeignKey(TextItem.id), primary_key=True)
        created_at = Column(DateTime)

    return Article
