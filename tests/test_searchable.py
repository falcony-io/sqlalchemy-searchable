# -*- coding: utf-8 -*-
from sqlalchemy_searchable import search
from tests import TestCase, TextItem, TextItemQuery, Article, Order


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

    def test_supports_catalog_parameter(self):
        query = TextItemQuery(TextItem, self.session)
        query = query.search(u'orrimorri', catalog='finnish')
        assert "to_tsquery(:to_tsquery_1, :to_tsquery_2)" in str(query)


class TestSearchFunction(TestCase):
    def test_supports_session_queries(self):
        query = self.session.query(Order)
        assert (
            '("order".search_vector) @@ to_tsquery(:to_tsquery_1)'
            in
            str(search(query, 'something'))
        )


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
