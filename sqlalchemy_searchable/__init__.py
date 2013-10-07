import re
from pyparsing import ParseException

import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.schema import DDL
from sqlalchemy_utils import TSVectorType
from .parser import SearchQueryParser, unicode_non_alnum


__version__ = '0.4.3'


parser = SearchQueryParser()


def parse_search_query(query, parser=parser):
    query = query.strip()
    # Convert hyphens between words to spaces but leave all hyphens which are
    # at the beginning of the word (negation operator)
    query = re.sub(r'(?i)(?<=[^\s|^])-(?=[^\s])', ' ', query)
    # Remove all illegal characters from the search query. Also remove multiple
    # spaces.
    query = re.sub(r'[%s]+' % unicode_non_alnum, ' ', query).strip()

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
    :param tablename: custom tablename
    :param language: language to be passed to to_tsquery
    """
    if not search_query:
        return query

    search_query = parse_search_query(search_query)
    if not search_query:
        return query

    entity = query._entities[0].entity_zero.class_

    search_vectors = inspect_search_vectors(entity)

    query = query.filter(
        search_vectors[0].match_tsquery(search_query, catalog=catalog)
    )
    return query.params(term=search_query)


def quote_identifier(identifier):
    """Adds double quotes to given identifier. Since PostgreSQL is the only
    supported dialect we don't need dialect specific stuff here"""
    return '"%s"' % identifier


class SearchManager():
    default_options = {
        'tablename': None,
        'search_trigger_name': '{table}_{column}_trigger',
        'search_index_name': '{table}_{column}_index',
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
        tablename = column.table.name
        search_index_name = self.option(column, 'search_index_name').format(
            table=tablename,
            column=column.name
        )
        return DDL(
            """
            CREATE INDEX {search_index_name} ON {table}
            USING gin({search_vector_name})
            """
            .format(
                table=quote_identifier(tablename),
                search_index_name=search_index_name,
                search_vector_name=column.name
            )
        )

    def search_trigger_ddl(self, column):
        """
        Returns the ddl for creating an automatically updated search trigger.

        :param column: TSVectorType typed SQLAlchemy column object
        """
        tablename = column.table.name
        search_trigger_name = self.option(
            column,
            'search_trigger_name'
        ).format(table=tablename, column=column.name)

        return DDL(
            """
            CREATE TRIGGER {search_trigger_name}
            BEFORE UPDATE OR INSERT ON {table}
            FOR EACH ROW EXECUTE PROCEDURE
            tsvector_update_trigger({arguments})
            """
            .format(
                search_trigger_name=search_trigger_name,
                table=quote_identifier(tablename),
                arguments=', '.join([
                    column.name,
                    "'%s'" % self.option(column, 'catalog')] +
                    list(column.type.columns)
                )
            )
        )

    def inspect_columns(self, cls):
        """
        Inspects all searchable columns for given class.

        :param cls: SQLAlchemy declarative class
        """
        return [
            column for column in cls.__table__.c
            if isinstance(column.type, TSVectorType)
        ]

    def define_triggers_and_indexes(self, mapper, cls):
        columns = self.inspect_columns(cls)
        for column in columns:
            # We don't want sqlalchemy to know about this column so we add it
            # externally.
            table = cls.__table__

            column_name = '%s_%s' % (table.name, column.name)

            if column_name in self.processed_columns:
                continue

            # This indexes the tsvector column.
            event.listen(
                table,
                'after_create',
                self.search_index_ddl(column)
            )

            # This sets up the trigger that keeps the tsvector column up to
            # date.
            if column.type.columns:
                event.listen(
                    table,
                    'after_create',
                    self.search_trigger_ddl(column)
                )

            self.processed_columns.append(column_name)


search_manager = SearchManager()


def make_searchable(
    mapper=sa.orm.mapper,
    manager=search_manager,
    options={}
):
    manager.options.update(options)
    event.listen(
        mapper, 'instrument_class', manager.define_triggers_and_indexes
    )
