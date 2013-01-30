import sqlalchemy as sa

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.query import Query
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_searchable import (
    Searchable, SearchQueryMixin, safe_search_terms
)

engine = create_engine(
    'postgres://postgres@localhost/sqlalchemy_searchable_test'
)
Base = declarative_base()


class TestCase(object):
    def setup_method(self, method):
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        self.session = Session()

    def teardown_method(self, method):
        self.session.close_all()
        Base.metadata.drop_all(engine)


class TextItemQuery(Query, SearchQueryMixin):
    pass


class TextItem(Base, Searchable):
    __searchable_columns__ = ['name', 'content']
    __search_options__ = {
        'tablename': 'textitem',
        'search_vector_name': 'search_vector',
        'search_trigger_name': '{table}_search_update',
        'search_index_name': '{table}_search_index',
    }
    __tablename__ = 'textitem'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    name = sa.Column(sa.Unicode(255))

    content = sa.Column(sa.UnicodeText)


class Article(TextItem):
    __tablename__ = 'article'
    id = sa.Column(sa.Integer, sa.ForeignKey(TextItem.id), primary_key=True)

    created_at = sa.Column(sa.DateTime)


class TestAutomaticallyCreatedSchemaItems(TestCase):
    def test_creates_search_index(self):
        rows = self.session.execute(
            """SELECT relname
            FROM pg_class
            WHERE oid IN (
                SELECT indexrelid
                FROM pg_index, pg_class
                WHERE pg_class.relname='textitem'
                    AND pg_class.oid=pg_index.indrelid
                    AND indisunique != 't'
                    AND indisprimary != 't'
            )"""
        ).fetchall()
        assert 'textitem_search_index' in map(lambda a: a[0], rows)

    def test_creates_search_trigger(self):
        rows = self.session.execute(
            """SELECT DISTINCT trigger_name
            FROM information_schema.triggers
            WHERE event_object_table = 'textitem'
            AND trigger_schema NOT IN
            ('pg_catalog', 'information_schema')"""
        ).fetchall()
        assert 'textitem_search_update' in map(lambda a: a[0], rows)

    def test_creates_search_vector_column(self):
        rows = self.session.execute(
            """SELECT column_name
            FROM information_schema.columns WHERE table_name = 'textitem'"""
        ).fetchall()
        assert 'search_vector' in map(lambda a: a[0], rows)


class TestSearchQueryMixin(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.session.add(TextItem(name=u'index', content=u'some content'))
        self.session.add(TextItem(name=u'admin', content=u'admin content'))
        self.session.add(
            TextItem(name=u'home', content=u'this is the home page')
        )
        self.session.commit()

    def test_searches_trhough_all_fulltext_indexed_fields(self):
        assert (
            TextItemQuery(TextItem, self.session)
            .search('admin').count() == 1
        )

    def test_search_supports_term_splitting(self):
        assert (
            TextItemQuery(TextItem, self.session)
            .search('content').count() == 2
        )

    def test_term_splitting_supports_multiple_spaces(self):
        query = TextItemQuery(TextItem, self.session)
        assert query.search('content  some').first().name == u'index'
        assert query.search('content   some').first().name == u'index'
        assert query.search('  ').count() == 3

    def test_search_removes_illegal_characters(self):
        assert TextItemQuery(TextItem, self.session).search(':!').count()

    def test_search_removes_stopword_characters(self):
        assert TextItemQuery(TextItem, self.session).search('@#').count()


class TestForeignCharacterSupport(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.session.add(TextItem(name=u'index', content=u'ähtäri örrimörri'))
        self.session.add(TextItem(name=u'admin', content=u'ahtari orrimorri'))
        self.session.commit()

    def test_search_supports_non_english_characters(self):
        query = TextItemQuery(TextItem, self.session)
        assert query.search(u'ähtäri').count() == 1
        query = TextItemQuery(TextItem, self.session)
        assert query.search(u'orrimorri').count() == 1


class TestSearchableInheritance(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.session.add(Article(name=u'index', content=u'some content'))
        self.session.add(Article(name=u'admin', content=u'admin content'))
        self.session.add(
            Article(name=u'home', content=u'this is the home page')
        )
        self.session.commit()

    def test_supports_inheritance(self):
        assert (
            TextItemQuery(Article, self.session)
            .search('content').count() == 2
        )


class TestSafeSearchTerms(object):
    def test_uses_pgsql_wildcard_by_default(self):
        assert safe_search_terms('star wars') == [
            'star:*', 'wars:*'
        ]

    def test_supports_custom_wildcards(self):
        assert safe_search_terms('star wars', wildcard='*') == [
            'star*', 'wars*'
        ]
