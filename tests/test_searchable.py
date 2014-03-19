# -*- coding: utf-8 -*-
from sqlalchemy_searchable import search
from tests import TestCase, create_test_cases


class SearchQueryMixinTestCase(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.session.add(
            self.TextItem(
                name=u'index',
                content=u'some content'
            )
        )
        self.session.add(
            self.TextItem(
                name=u'admin',
                content=u'admin content'
            )
        )
        self.session.add(
            self.TextItem(
                name=u'home',
                content=u'this is the home page of someone@example.com'
            )
        )
        self.session.commit()

    def test_searches_through_all_fulltext_indexed_fields(self):
        assert (
            self.TextItemQuery(self.TextItem, self.session)
            .search('admin').count() == 1
        )

    def test_search_supports_term_splitting(self):
        assert (
            self.TextItemQuery(self.TextItem, self.session)
            .search('content').count() == 2
        )

    def test_term_splitting_supports_multiple_spaces(self):
        query = self.TextItemQuery(self.TextItem, self.session)
        assert query.search('content  some').first().name == u'index'
        assert query.search('content   some').first().name == u'index'
        assert query.search('  ').count() == 3

    def test_search_removes_illegal_characters(self):
        assert self.TextItemQuery(
            self.TextItem, self.session
        ).search(':!').count()

    def test_search_removes_stopword_characters(self):
        assert self.TextItemQuery(
            self.TextItem, self.session
        ).search('@#').count()

    def test_search_by_email(self):
        assert self.TextItemQuery(
            self.TextItem, self.session
        ).search('someone@example.com').count()

    def test_supports_catalog_parameter(self):
        query = self.TextItemQuery(self.TextItem, self.session)
        query = query.search(u'orrimorri', catalog='finnish')
        assert "to_tsquery(:to_tsquery_1, :to_tsquery_2)" in str(query)


create_test_cases(SearchQueryMixinTestCase)


class TestSearchFunction(TestCase):
    def test_supports_session_queries(self):
        query = self.session.query(self.Order)
        assert (
            '("order".search_vector) @@ to_tsquery(:to_tsquery_1)'
            in
            str(search(query, 'something'))
        )


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
