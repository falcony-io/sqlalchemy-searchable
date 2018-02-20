# -*- coding: utf-8 -*-
from sqlalchemy_searchable import search, search_manager
from tests import create_test_cases, TestCase


class SearchQueryMixinTestCase(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.items = [
            self.TextItem(
                name=u'index',
                content=u'some content'
            ),
            self.TextItem(
                name=u'admin',
                content=u'admin content'
            ),
            self.TextItem(
                name=u'home',
                content=u'this is the home page of someone@example.com'
            ),
            self.TextItem(
                name=u'not a some content',
                content=u'not a name'
            )
        ]
        self.session.add_all(self.items)
        self.session.commit()

    def test_searches_through_all_fulltext_indexed_fields(self):
        assert (
            self.TextItemQuery(self.TextItem, self.session)
            .search('admin').count() == 1
        )

    def test_search_supports_term_splitting(self):
        assert (
            self.TextItemQuery(self.TextItem, self.session)
            .search('content').count() == 3
        )

    def test_term_splitting_supports_multiple_spaces(self):
        query = self.TextItemQuery(self.TextItem, self.session)
        assert query.search('content  some').first().name == u'index'
        assert query.search('content   some').first().name == u'index'
        assert query.search('  ').count() == 4

    def test_search_by_email(self):
        assert self.TextItemQuery(
            self.TextItem, self.session
        ).search('someone@example.com').count()

    def test_supports_regconfig_parameter(self):
        query = self.TextItemQuery(self.TextItem, self.session)
        query = query.search(u'orrimorri', regconfig='finnish')
        assert "tsq_parse(%(tsq_parse_1)s, %(tsq_parse_2)s)" in str(
            query.statement.compile(self.session.bind)
        )

    def test_supports_vector_parameter(self):
        vector = self.TextItem.content_search_vector
        query = self.TextItemQuery(self.TextItem, self.session)
        query = query.search('content', vector=vector)
        assert query.count() == 2

    def test_search_specific_columns(self):
        query = search(self.session.query(self.TextItem.id), 'admin')
        assert query.count() == 1

    def test_sorted_search_results(self):
        query = self.TextItemQuery(self.TextItem, self.session)
        sorted_results = query.search('some content', sort=True).all()
        assert sorted_results == self.items[0:2] + [self.items[3]]


class TestUsesGlobalConfigOptionsAsFallbacks(TestCase):
    def setup_method(self, method):
        search_manager.options['regconfig'] = 'pg_catalog.simple'
        TestCase.setup_method(self, method)
        self.items = [
            self.TextItem(
                name=u'index',
                content=u'some content'
            ),
            self.TextItem(
                name=u'admin',
                content=u'admin content'
            ),
            self.TextItem(
                name=u'home',
                content=u'this is the home page of someone@example.com'
            ),
            self.TextItem(
                name=u'not a some content',
                content=u'not a name'
            )
        ]
        self.session.add_all(self.items)
        self.session.commit()

    def teardown_method(self, method):
        TestCase.teardown_method(self, method)
        search_manager.options['regconfig'] = 'pg_catalog.english'

    def test_uses_global_regconfig_as_fallback(self):
        query = search(self.session.query(self.TextItem.id), 'the')
        assert query.count() == 1


create_test_cases(SearchQueryMixinTestCase)


class TestSearchableInheritance(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.session.add(self.Article(name=u'index', content=u'some content'))
        self.session.add(self.Article(name=u'admin', content=u'admin content'))
        self.session.add(
            self.Article(name=u'home', content=u'this is the home page')
        )
        self.session.commit()

    def test_supports_inheritance(self):
        assert (
            self.TextItemQuery(self.Article, self.session)
            .search('content').count() == 2
        )
