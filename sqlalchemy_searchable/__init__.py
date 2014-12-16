import re
from pyparsing import ParseException

import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.schema import DDL
from sqlalchemy_utils import TSVectorType
from .parser import SearchQueryParser


__version__ = '0.7.1'


parser = SearchQueryParser()


def parse_search_query(query, parser=parser):
    query = query.strip()
    # Convert hyphens between words to spaces but leave all hyphens which are
    # at the beginning of the word (negation operator)
    query = re.sub(r'(?i)(?<=[^\s|^])-(?=[^\s])', ' ', query)

    parts = query.split()
    parts = [
        parser.remove_special_chars(part).strip() for part in parts if part
    ]
    query = ' '.join(parts)
    if not query:
        return u''
    try:
        return parser.parse(query)
    except ParseException:
        return u''


class SearchQueryMixin(object):
    def search(self, search_query, catalog=None):
        """
        Search given query with full text search.

        :param search_query: the search query
        """
        return search(self, search_query, catalog=catalog)


def inspect_search_vectors(entity):
    search_vectors = []
    for prop in entity.__mapper__.iterate_properties:
        if isinstance(prop, sa.orm.ColumnProperty):
            if isinstance(prop.columns[0].type, TSVectorType):
                search_vectors.append(getattr(entity, prop.key))
    return search_vectors


def search(query, search_query, vector=None, catalog=None):
    """
    Search given query with full text search.

    :param search_query: the search query
    :param vector: search vector to use
    :param catalog: postgresql catalog to be used
    """
    if not search_query:
        return query

    search_query = parse_search_query(search_query)
    if not search_query:
        return query

    entity = query._entities[0].entity_zero.class_

    if not vector:
        search_vectors = inspect_search_vectors(entity)
        vector = search_vectors[0]

    query = query.filter(
        vector.match_tsquery(search_query, catalog=catalog)
    )
    return query.params(term=search_query)


def quote_identifier(identifier):
    """Adds double quotes to given identifier. Since PostgreSQL is the only
    supported dialect we don't need dialect specific stuff here"""
    return '"%s"' % identifier


class SQLConstruct(object):
    def __init__(self, tsvector_column, indexed_columns=None, options=None):
        self.table = tsvector_column.table
        self.tsvector_column = tsvector_column
        self.options = self.init_options(options)
        if indexed_columns:
            self.indexed_columns = list(indexed_columns)
        else:
            self.indexed_columns = list(self.tsvector_column.type.columns)

    def init_options(self, options=None):
        if not options:
           options = {}
        for key, value in SearchManager.default_options.items():
            try:
                option = self.tsvector_column.type.options[key]
            except (KeyError, AttributeError):
                option = value
            options.setdefault(key, option)
        return options

    @property
    def table_name(self):
        if self.table.schema:
            return '%s."%s"' % (self.table.schema, self.table.name)
        else:
            return '"' + self.table.name + '"'

    @property
    def search_index_name(self):
        return self.options['search_index_name'].format(
            table=self.table.name,
            column=self.tsvector_column.name
        )

    @property
    def search_function_name(self):
        return self.options['search_trigger_function_name'].format(
            table=self.table.name,
            column=self.tsvector_column.name
        )

    @property
    def search_trigger_name(self):
        return self.options['search_trigger_name'].format(
            table=self.table.name,
            column=self.tsvector_column.name
        )

    def format_column(self, column_name):
        value = "COALESCE(NEW.%s, '')" % column_name
        if self.options['remove_symbols']:
            value = "REGEXP_REPLACE(%s, '[%s]', ' ', 'g')" % (
                value,
                self.options['remove_symbols']
            )
        return "%s, ' '" % value

    @property
    def search_function_args(self):
        return 'CONCAT(%s)' % ', '.join(
            self.format_column(column_name)
            for column_name in self.indexed_columns
        )


class CreateSearchFunctionSQL(SQLConstruct):
    def __str__(self):
        return (
            """CREATE FUNCTION
                {search_trigger_function_name}() RETURNS TRIGGER AS $$
            BEGIN
                NEW.{search_vector_name} = to_tsvector(
                    {arguments}
                );
                RETURN NEW;
            END
            $$ LANGUAGE 'plpgsql';
            """
        ).format(
            search_trigger_function_name=self.search_function_name,
            search_vector_name=self.tsvector_column.name,
            arguments="'%s', %s" % (
                self.options['catalog'],
                self.search_function_args
            )
        )


class CreateSearchTriggerSQL(SQLConstruct):
    @property
    def search_trigger_function_with_trigger_args(self):
        if self.options['remove_symbols']:
            return self.search_function_name + '()'
        return 'tsvector_update_trigger({arguments})'.format(
            arguments=', '.join(
                [
                    self.tsvector_column.name,
                    "'%s'" % self.options['catalog']
                ] +
                self.indexed_columns
            )
        )

    def __str__(self):
        return (
            "CREATE TRIGGER {search_trigger_name}"
            " BEFORE UPDATE OR INSERT ON {table}"
            " FOR EACH ROW EXECUTE PROCEDURE"
            " {procedure_ddl}"
            .format(
                search_trigger_name=self.search_trigger_name,
                table=self.table_name,
                procedure_ddl=
                self.search_trigger_function_with_trigger_args
            )
        )


class CreateSearchIndexSQL(SQLConstruct):
    def __str__(self):
        return (
            "CREATE INDEX {search_index_name} ON {table}"
            " USING gin({search_vector_name})"
            .format(
                table=self.table_name,
                search_index_name=self.search_index_name,
                search_vector_name=self.tsvector_column.name
            )
        )


class DropSearchFunctionSQL(SQLConstruct):
    def __str__(self):
        return 'DROP FUNCTION IF EXISTS %s()' % self.search_function_name


class DropSearchTriggerSQL(SQLConstruct):
    def __str__(self):
        return 'DROP TRIGGER IF EXISTS %s ON %s' % (
            self.search_trigger_name,
            self.table_name
        )


class SearchManager():
    default_options = {
        'tablename': None,
        'remove_symbols': '-@.',
        'search_trigger_name': '{table}_{column}_trigger',
        'search_index_name': '{table}_{column}_index',
        'search_trigger_function_name': '{table}_{column}_update',
        'catalog': 'pg_catalog.english'
    }

    def __init__(self, options={}):
        self.options = self.default_options
        self.options.update(options)
        self.processed_columns = []

    def option(self, column, name):
        try:
            return column.type.options[name]
        except (AttributeError, KeyError):
            return self.options[name]

    def search_index_ddl(self, column):
        """
        Returns the ddl for creating the actual search index.

        :param column: TSVectorType typed SQLAlchemy column object
        """
        return DDL(str(CreateSearchIndexSQL(column)))

    def search_function_ddl(self, column):
        return DDL(str(CreateSearchFunctionSQL(column)))

    def search_trigger_ddl(self, column):
        """
        Returns the ddl for creating an automatically updated search trigger.

        :param column: TSVectorType typed SQLAlchemy column object
        """
        return DDL(str(CreateSearchTriggerSQL(column)))

    def inspect_columns(self, cls):
        """
        Inspects all searchable columns for given class.

        :param cls: SQLAlchemy declarative class
        """
        return [
            column for column in cls.__table__.c
            if isinstance(column.type, TSVectorType)
        ]

    def append_index(self, cls, column):
        if not hasattr(cls, '__table_args__') or cls.__table_args__ is None:
            cls.__table_args__ = []
        cls.__table_args__ = list(cls.__table_args__).append(
            sa.Index(
                '_'.join(('ix', column.table.name, column.name)),
                column,
                postgresql_using='gin'
            )
        )

    def attach_ddl_listeners(self, mapper, cls):
        columns = self.inspect_columns(cls)
        for column in columns:
            table = cls.__table__

            column_name = '%s_%s' % (table.name, column.name)

            if column_name in self.processed_columns:
                continue

            self.append_index(cls, column)

            # This sets up the trigger that keeps the tsvector column up to
            # date.
            if column.type.columns:
                if self.option(column, 'remove_symbols'):
                    event.listen(
                        table,
                        'after_create',
                        self.search_function_ddl(column)
                    )
                    event.listen(
                        table,
                        'after_drop',
                        DDL(str(DropSearchFunctionSQL(column)))
                    )
                event.listen(
                    table,
                    'after_create',
                    self.search_trigger_ddl(column)
                )

            self.processed_columns.append(column_name)


search_manager = SearchManager()


def sync_trigger(
    conn,
    table_name,
    tsvector_column,
    indexed_columns,
    options=None
):
    """
    Synchronizes search trigger and trigger function for given table and given
    search index column. Internally this function executes the following SQL
    queries:

    * Drops search trigger for given table (if it exists)
    * Drops search function for given table (if it exists)
    * Creates search function for given table
    * Creates search trigger for given table
    * Updates all rows for given search vector by running a column=column
      update query for given table.


    Example::

        from sqlalchemy_searchable import sync_trigger


        sync_trigger(
            conn,
            'article',
            'search_vector',
            ['name', 'content']
        )


    This function is especially useful when working with alembic migrations.
    In the following example we add a content column to article table and then
    sync the trigger to contain this new column::

        # ... some alembic setup

        from alembic import op
        from sqlalchemy_searchable import sync_trigger


        def upgrade():
            conn = op.get_bind()
            op.add_column('article', sa.Column('content', sa.Text))

            sync_trigger(conn, 'article', 'search_vector', ['name', 'content'])

        # ... same for downgrade


    :param conn: SQLAlchemy Connection object
    :param table_name: name of the table to apply search trigger syncing
    :param tsvector_column:
        TSVector typed column which is used as the search index column
    :param indexed_columns:
        Full text indexed column names as a list
    :param options: Dictionary of configuration options
    """
    meta = sa.MetaData()
    table = sa.Table(
        table_name,
        meta,
        autoload=True,
        autoload_with=conn
    )
    params = dict(
        tsvector_column=getattr(table.c, tsvector_column),
        indexed_columns=indexed_columns,
        options=options
    )
    classes = [
        DropSearchTriggerSQL,
        DropSearchFunctionSQL,
        CreateSearchFunctionSQL,
        CreateSearchTriggerSQL,
    ]
    for class_ in classes:
        conn.execute(str(class_(**params)))
    update_sql = table.update().values(
        {indexed_columns[0]: sa.text(indexed_columns[0])}
    )
    conn.execute(update_sql)


def make_searchable(
    mapper=sa.orm.mapper,
    manager=search_manager,
    options={}
):
    manager.options.update(options)
    event.listen(
        mapper, 'instrument_class', manager.attach_ddl_listeners
    )
