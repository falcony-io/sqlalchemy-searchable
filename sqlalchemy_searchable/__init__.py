import re
from pyparsing import ParseException

from sqlalchemy import event
from sqlalchemy.schema import DDL
from sqlalchemy.orm.mapper import Mapper
from .parser import SearchQueryParser, unicode_non_letters


__version__ = '0.3.1'


parser = SearchQueryParser()


def parse_search_query(query, parser=parser):
    # Remove all illegal characters from the search query. Also remove multiple
    # spaces.
    query = re.sub(r'[%s]+' % unicode_non_letters, ' ', query).strip()

    if not query:
        return u''

    try:
        return parser.parse(query)
    except ParseException:
        return u''


class SearchQueryMixin(object):
    def search_filter(self, term, tablename=None, language=None):
        return search_filter(self, term, tablename, language)

    def search(self, search_query, tablename=None, language=None):
        """
        Search given query with full text search.

        :param search_query: the search query
        :param tablename: custom tablename
        :param language: language to be passed to to_tsquery
        """
        if not search_query:
            return self

        query = parse_search_query(search_query)
        if not query:
            return self

        return (
            self.filter(
                self.search_filter(search_query, tablename, language)
            )
            .params(term=query)
        )


def search_filter(query, term, tablename=None, language=None):
    if not tablename:
        mapper = query._entities[0].entity_zero
        entity = mapper.class_

        try:
            tablename = entity.__search_options__['tablename']
        except (AttributeError, KeyError):
            tablename = manager.inspect_searchable_tablename(entity)

    if not language:
        language = manager.option(mapper.class_, 'catalog').split('.')[-1]

    if not language:
        return '%s.search_vector @@ to_tsquery(:term)' % (
            quote_identifier(tablename)
        )
    else:
        return "%s.search_vector @@ to_tsquery('%s', :term)" % (
            quote_identifier(tablename), language
        )


def search(query, search_query, tablename=None, language=None):
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

    if hasattr(query, 'search_filter'):
        query = query.filter(
            query.search_filter(search_query, tablename, language)
        )
    else:
        query = query.filter(
            search_filter(query, search_query, tablename, language)
        )
    return query.params(term=search_query)


def quote_identifier(identifier):
    """Adds double quotes to given identifier. Since PostgreSQL is the only
    supported dialect we don't need dialect specific stuff here"""
    return '"%s"' % identifier


def attach_search_indexes(mapper, class_):
    if hasattr(class_, '__searchable_columns__'):
        manager.define_search_vector(class_)


event.listen(Mapper, 'instrument_class', attach_search_indexes)


class SearchManager():
    default_options = {
        'tablename': None,
        'search_vector_name': 'search_vector',
        'search_trigger_name': '{table}_search_update',
        'search_index_name': '{table}_search_index',
        'catalog': 'pg_catalog.english'
    }

    def __init__(self, options={}):
        self.options = self.default_options
        self.options.update(options)

    def option(self, obj, name):
        try:
            return obj.__search_options__[name]
        except (AttributeError, KeyError):
            return self.options[name]

    def inspect_searchable_tablename(self, cls):
        """
        Recursive method that returns the name of the searchable table. This is
        method is needed for the inspection of tablenames in certain
        inheritance scenarios such as joined table inheritance where only
        parent is defined is searchable.
        """
        if Searchable in cls.__bases__:
            return cls.__tablename__

        for class_ in cls.__bases__:
            return class_._inspect_searchable_tablename()

    def search_index_ddl(self, cls):
        """
        Returns the ddl for creating the actual search index.
        """
        tablename = cls.__tablename__
        search_vector_name = self.option(cls, 'search_vector_name')
        search_index_name = self.option(cls, 'search_index_name').format(
            table=tablename
        )
        return DDL(
            """
            CREATE INDEX {search_index_name} ON {table}
            USING gin({search_vector_name})
            """
            .format(
                table=quote_identifier(tablename),
                search_index_name=search_index_name,
                search_vector_name=search_vector_name
            )
        )

    def search_trigger_ddl(self, cls):
        """
        Returns the ddl for creating an automatically updated search trigger.
        """
        tablename = cls.__tablename__
        search_vector_name = self.option(cls, 'search_vector_name')
        search_trigger_name = self.option(
            cls,
            'search_trigger_name'
        ).format(table=tablename)

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
                    search_vector_name,
                    "'%s'" % self.option(cls, 'catalog')] +
                    cls.__searchable_columns__
                )
            )
        )

    def define_search_vector(self, cls):
        # In order to support joined table inheritance we need to ensure that
        # this class directly inherits Searchable.
        if Searchable not in cls.__bases__:
            return

        if not cls.__searchable_columns__:
            raise Exception(
                "No searchable columns defined for model %s" % cls.__name__
            )

        # We don't want sqlalchemy to know about this column so we add it
        # externally.
        table = cls.__table__

        # This indexes the tsvector column.
        event.listen(
            table,
            'after_create',
            self.search_index_ddl(cls)
        )

        # This sets up the trigger that keeps the tsvector column up to date.
        event.listen(
            table,
            'after_create',
            self.search_trigger_ddl(cls)
        )


manager = SearchManager()


class Searchable(object):
    __searchable_columns__ = {}
