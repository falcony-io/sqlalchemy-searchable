import dataclasses
import os
from collections.abc import Sequence
from functools import reduce
from typing import Any, cast, Literal, TypeVar

import sqlalchemy as sa
from sqlalchemy import (
    Column,
    ColumnClause,
    ColumnElement,
    Connection,
    event,
    FromClause,
    Select,
)
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapper
from sqlalchemy.schema import DDL, DDLElement
from sqlalchemy.sql.compiler import SQLCompiler
from sqlalchemy.sql.expression import Executable
from sqlalchemy_utils import TSVectorType

from .vectorizers import Vectorizer

__version__ = "3.0.0"


@dataclasses.dataclass(frozen=True)
class SearchOptions:
    """
    Configuration options for full-text search functionality.

    This dataclass provides configuration settings for PostgreSQL full-text search
    triggers, functions, and indexing behavior. All instances are immutable (frozen).
    """

    #: Template string for the search trigger name. Available placeholders are
    #: ``{table}`` and ``{column}``.
    search_trigger_name: str = "{table}_{column}_trigger"

    #: Template string for the search trigger function name. Available placeholders
    #: are ``{table}`` and ``{column}``.
    search_trigger_function_name: str = "{table}_{column}_update"

    #: PostgreSQL text search configuration name. This determines the language-specific
    #: rules for stemming and stop words.
    regconfig: str = "pg_catalog.english"

    #: Dictionary mapping column names to their search weights (A, B, C, or D), where
    #: A is the highest weight and D is the lowest. This affects relevance ranking in
    #: search results.
    weights: dict[str, Literal["A", "B", "C", "D"]] = dataclasses.field(
        default_factory=dict
    )

    #: Whether to automatically create a GIN index on the search vector column.
    auto_index: bool = True


vectorizer = Vectorizer()
"""
An instance of :class:`Vectorizer` that keeps a track of the registered vectorizers. Use
this as a decorator to register a function as a vectorizer.
"""


def inspect_search_vectors(entity: Any) -> list[Any]:
    return [
        getattr(entity, key).property.columns[0]
        for key, column in sa.inspect(entity).columns.items()
        if isinstance(column.type, TSVectorType)
    ]


_T = TypeVar("_T", bound=tuple[Any, ...])


def search(
    query: Select[_T],
    search_query: str,
    vector: Column[TSVectorType] | None = None,
    regconfig: str | None = None,
    sort: bool = False,
) -> Select[_T]:
    """
    Search given query with full text search.

    :param search_query: the search query
    :param vector: search vector to use
    :param regconfig: postgresql regconfig to be used
    :param sort: Order the results by relevance. This uses `cover density`_ ranking
        algorithm (``ts_rank_cd``) for sorting.

    .. _cover density: https://www.postgresql.org/docs/devel/textsearch-controls.html#TEXTSEARCH-RANKING
    """
    if not search_query.strip():
        return query

    if vector is None:
        entity = query.column_descriptions[0]["entity"]
        search_vectors = inspect_search_vectors(entity)
        vector = search_vectors[0]

    if regconfig is None:
        regconfig = search_manager.options.regconfig

    query = query.filter(
        vector.op("@@")(sa.func.parse_websearch(regconfig, search_query))
    )
    if sort:
        query = query.order_by(
            sa.desc(sa.func.ts_rank_cd(vector, sa.func.parse_websearch(search_query)))
        )

    return query.params(term=search_query)


class SQLConstruct:
    def __init__(
        self,
        tsvector_column: Column[Any],
        indexed_columns: Sequence[str] | None = None,
        options: SearchOptions | None = None,
    ):
        self.table = tsvector_column.table
        self.tsvector_column = tsvector_column
        self.search_options = options or SearchOptions()
        if indexed_columns:
            self.indexed_columns = list(indexed_columns)
        elif hasattr(self.tsvector_column.type, "columns"):
            self.indexed_columns = list(self.tsvector_column.type.columns)
        else:
            self.indexed_columns = []

    @property
    def table_name(self) -> str:
        if self.table.schema:
            return f'{self.table.schema}."{self.table.name}"'
        else:
            return '"' + self.table.name + '"'

    @property
    def search_function_name(self) -> str:
        return self.search_options.search_trigger_function_name.format(
            table=self.table.name, column=self.tsvector_column.name
        )

    @property
    def search_trigger_name(self) -> str:
        return self.search_options.search_trigger_name.format(
            table=self.table.name, column=self.tsvector_column.name
        )

    def column_vector(self, column: Column[Any]) -> ColumnElement[str]:
        column_reference: ColumnClause[Any] = sa.literal_column(f"NEW.{column.name}")
        try:
            vectorizer_func = vectorizer[column]
        except KeyError:
            value: ColumnElement[Any] = column_reference
        else:
            value = vectorizer_func(column_reference)
        tsvector = sa.func.to_tsvector(
            sa.literal(self.search_options.regconfig),
            sa.func.coalesce(value, sa.text("''")),
        )
        if column.name in self.search_options.weights:
            weight = self.search_options.weights[column.name]
            return sa.func.setweight(tsvector, weight)
        return tsvector

    def search_vector(self, compiler: SQLCompiler) -> str:
        vectors = (
            self.column_vector(getattr(self.table.c, column_name))
            for column_name in self.indexed_columns
        )
        concatenated = reduce(lambda x, y: x.op("||")(y), vectors)
        return compiler.sql_compiler.process(concatenated, literal_binds=True)


class CreateSearchFunctionSQL(SQLConstruct, DDLElement, Executable):
    pass


@compiles(CreateSearchFunctionSQL)
def compile_create_search_function_sql(
    element: CreateSearchFunctionSQL,
    compiler: SQLCompiler,
) -> str:
    return f"""CREATE FUNCTION
            {element.search_function_name}() RETURNS TRIGGER AS $$
        BEGIN
            NEW.{element.tsvector_column.name} = {element.search_vector(compiler)};
            RETURN NEW;
        END
        $$ LANGUAGE 'plpgsql';
        """


class CreateSearchTriggerSQL(SQLConstruct, DDLElement, Executable):
    @property
    def search_trigger_function_with_trigger_args(self) -> str:
        if self.search_options.weights or any(
            getattr(self.table.c, column) in vectorizer
            for column in self.indexed_columns
        ):
            return self.search_function_name + "()"
        return "tsvector_update_trigger({arguments})".format(
            arguments=", ".join(
                [self.tsvector_column.name, f"'{self.search_options.regconfig}'"]
                + self.indexed_columns
            )
        )


@compiles(CreateSearchTriggerSQL)
def compile_create_search_trigger_sql(
    element: CreateSearchTriggerSQL,
    compiler: SQLCompiler,
) -> str:
    return (
        f"CREATE TRIGGER {element.search_trigger_name}"
        f" BEFORE UPDATE OR INSERT ON {element.table_name}"
        " FOR EACH ROW EXECUTE PROCEDURE"
        f" {element.search_trigger_function_with_trigger_args}"
    )


class DropSearchFunctionSQL(SQLConstruct, DDLElement, Executable):
    pass


@compiles(DropSearchFunctionSQL)
def compile_drop_search_function_sql(
    element: DropSearchFunctionSQL,
    compiler: SQLCompiler,
) -> str:
    return f"DROP FUNCTION IF EXISTS {element.search_function_name}()"


class DropSearchTriggerSQL(SQLConstruct, DDLElement, Executable):
    pass


@compiles(DropSearchTriggerSQL)
def compile_drop_search_trigger_sql(
    element: DropSearchTriggerSQL,
    compiler: SQLCompiler,
) -> str:
    return (
        f"DROP TRIGGER IF EXISTS {element.search_trigger_name} ON {element.table_name}"
    )


class SearchManager:
    def __init__(self, options: SearchOptions | None = None):
        self.options = options or SearchOptions()
        self.processed_columns: list[Column[TSVectorType]] = []
        self.listeners: list[tuple[sa.Table, str, DDLElement]] = []

    def inspect_columns(self, from_clause: FromClause) -> list[Column[TSVectorType]]:
        """
        Inspects all searchable columns for given class.

        :param table: SQLAlchemy Table
        """
        return [
            column
            for column in from_clause.columns
            if isinstance(column, Column) and isinstance(column.type, TSVectorType)
        ]

    def append_index(self, column: Column[Any]) -> None:
        sa.Index(
            "_".join(("ix", column.table.name, column.name)),
            column,
            postgresql_using="gin",
        )

    def process_mapper(self, mapper: Mapper[Any], cls: type[Any]) -> None:
        columns = self.inspect_columns(mapper.persist_selectable)
        for column in columns:
            if column in self.processed_columns:
                continue

            tsvector_type = cast(TSVectorType, column.type)
            options = dataclasses.replace(self.options, **tsvector_type.options)
            if options.auto_index:
                self.append_index(column)

            self.processed_columns.append(column)

    def add_listener(self, args: tuple[sa.Table, str, DDLElement]) -> None:
        self.listeners.append(args)
        event.listen(*args)

    def remove_listeners(self) -> None:
        for listener in self.listeners:
            event.remove(*listener)
        self.listeners = []

    def attach_ddl_listeners(self) -> None:
        # Remove all previously added listeners, so that same listener don't
        # get added twice in situations where class configuration happens in
        # multiple phases (issue #31).
        self.remove_listeners()

        for column in self.processed_columns:
            # This sets up the trigger that keeps the tsvector column up to
            # date.
            tsvector_type = cast(TSVectorType, column.type)
            if tsvector_type.columns:
                table = column.table
                options = dataclasses.replace(self.options, **tsvector_type.options)
                if options.weights or vectorizer.contains_tsvector(column):
                    self.add_listener(
                        (
                            table,
                            "after_create",
                            CreateSearchFunctionSQL(column, options=options),
                        )
                    )
                    self.add_listener(
                        (
                            table,
                            "after_drop",
                            DropSearchFunctionSQL(column, options=options),
                        )
                    )
                self.add_listener(
                    (
                        table,
                        "after_create",
                        CreateSearchTriggerSQL(column, options=options),
                    )
                )


search_manager = SearchManager()


def sync_trigger(
    conn: Connection,
    table_name: str,
    tsvector_column: str,
    indexed_columns: list[str],
    metadata: sa.MetaData | None = None,
    options: SearchOptions | None = None,
    schema: str | None = None,
    update_rows: bool = True,
) -> None:
    """Synchronize the search trigger and trigger function for the given table and
    search vector column. Internally, this function executes the following SQL
    queries:

    - Drop the search trigger for the given table and column if it exists.
    - Drop the search function for the given table and column if it exists.
    - Create the search function for the given table and column.
    - Create the search trigger for the given table and column.
    - Update all rows for the given search vector by executing a column=column update
      query for the given table.

    Example::

        from sqlalchemy_searchable import sync_trigger


        sync_trigger(
            conn,
            'article',
            'search_vector',
            ['name', 'content']
        )

    This function is especially useful when working with Alembic migrations. In the
    following example, we add a ``content`` column to the ``article`` table and then
    synchronize the trigger to contain this new column::

        from alembic import op
        import sqlalchemy as sa
        from sqlalchemy_searchable import sync_trigger


        def upgrade() -> None:
            conn = op.get_bind()
            op.add_column('article', sa.Column('content', sa.Text))

            sync_trigger(conn, 'article', 'search_vector', ['name', 'content'])

        # ... same for downgrade

    If you are using vectorizers, you need to initialize them in your migration
    file and pass them to this function::

        from typing import Any

        import sqlalchemy as sa
        from alembic import op
        from sqlalchemy.dialects.postgresql import HSTORE
        from sqlalchemy.orm import Mapped
        from sqlalchemy_searchable import sync_trigger, vectorizer


        def upgrade() -> None:
            vectorizer.clear()

            conn = op.get_bind()
            op.add_column('article', sa.Column('name_translations', HSTORE))

            metadata = sa.MetaData()
            articles = sa.Table('article', metadata, autoload_with=conn)

            @vectorizer(articles.c.name_translations)
            def hstore_vectorizer(
                column: sa.ColumnClause[Any],
            ) -> sa.ColumnElement[str]:
                return sa.cast(sa.func.avals(column), sa.Text)

            op.add_column('article', sa.Column('content', sa.Text))
            sync_trigger(
                conn,
                'article',
                'search_vector',
                ['name_translations', 'content'],
                metadata=metadata
            )

        # ... same for downgrade

    :param conn: SQLAlchemy Connection object
    :param table_name: name of the table to apply search trigger syncing
    :param tsvector_column:
        TSVector typed column which is used as the search index column
    :param indexed_columns:
        Full text indexed column names as a list
    :param metadata:
        Optional SQLAlchemy metadata object that is being used for autoloaded
        Table. If None is given, then a new MetaData object is initialized within
        this function.
    :param options: :class:`SearchOptions` instance for configuration
    :param schema: The schema name for this table. Defaults to ``None``.
    :param update_rows:
        If set to False, the values in the vector column will remain unchanged
        until one of the indexed columns is updated.
    """
    if metadata is None:
        metadata = sa.MetaData()
    table = sa.Table(
        table_name,
        metadata,
        autoload_with=conn,
        schema=schema,
    )
    params = dict(
        tsvector_column=getattr(table.c, tsvector_column),
        indexed_columns=indexed_columns,
        options=options,
    )
    classes = [
        DropSearchTriggerSQL,
        DropSearchFunctionSQL,
        CreateSearchFunctionSQL,
        CreateSearchTriggerSQL,
    ]
    for class_ in classes:
        conn.execute(class_(**params))

    if update_rows:
        update_sql = table.update().values(
            {indexed_columns[0]: sa.text(indexed_columns[0])}
        )
        conn.execute(update_sql)


def drop_trigger(
    conn: Connection,
    table_name: str,
    tsvector_column: str,
    metadata: sa.MetaData | None = None,
    options: SearchOptions | None = None,
    schema: str | None = None,
) -> None:
    """
    Drop the search trigger and trigger function for the given table and
    search vector column. Internally, this function executes the following SQL
    queries:

    - Drop the search trigger for the given table if it exists.
    - Drop the search function for the given table if it exists.

    Example::

        from alembic import op
        from sqlalchemy_searchable import drop_trigger


        def downgrade() -> None:
            conn = op.get_bind()

            drop_trigger(conn, 'article', 'search_vector')
            op.drop_index('ix_article_search_vector', table_name='article')
            op.drop_column('article', 'search_vector')

    :param conn: SQLAlchemy Connection object
    :param table_name: name of the table to apply search trigger dropping
    :param tsvector_column:
        TSVector typed column which is used as the search index column
    :param metadata:
        Optional SQLAlchemy metadata object that is being used for autoloaded
        Table. If None is given, then a new MetaData object is initialized within
        this function.
    :param options: :class:`SearchOptions` instance for configuration
    :param schema: The schema name for this table. Defaults to ``None``.
    """
    if metadata is None:
        metadata = sa.MetaData()
    table = sa.Table(
        table_name,
        metadata,
        autoload_with=conn,
        schema=schema,
    )
    params = dict(tsvector_column=getattr(table.c, tsvector_column), options=options)
    classes = [
        DropSearchTriggerSQL,
        DropSearchFunctionSQL,
    ]
    for class_ in classes:
        conn.execute(class_(**params))


path = os.path.dirname(os.path.abspath(__file__))


with open(os.path.join(path, "expressions.sql")) as file:
    sql_expressions = DDL(file.read())  # type: ignore[no-untyped-call]


def make_searchable(
    metadata: sa.MetaData,
    mapper: type[Mapper[Any]] = Mapper,
    manager: SearchManager = search_manager,
    options: SearchOptions | None = None,
) -> None:
    """
    Configure SQLAlchemy-Searchable for given SQLAlchemy metadata object.

    :param metadata: SQLAlchemy metadata object
    :param options: :class:`SearchOptions` instance for configuration
    """
    if options:
        manager.options = options
    event.listen(mapper, "instrument_class", manager.process_mapper)
    event.listen(mapper, "after_configured", manager.attach_ddl_listeners)
    event.listen(metadata, "before_create", sql_expressions)


def remove_listeners(
    metadata: sa.MetaData,
    manager: SearchManager = search_manager,
    mapper: type[Mapper[Any]] = Mapper,
) -> None:
    event.remove(mapper, "instrument_class", manager.process_mapper)
    event.remove(mapper, "after_configured", manager.attach_ddl_listeners)
    manager.remove_listeners()
    event.remove(metadata, "before_create", sql_expressions)
