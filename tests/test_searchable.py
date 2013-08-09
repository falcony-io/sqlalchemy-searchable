# -*- coding: utf-8 -*-
from sqlalchemy_searchable import search_filter, search
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

    def test_works_without_tablename_defined(self):
        del TextItem.__search_options__
        query = TextItemQuery(TextItem, self.session)
        assert query.search('content').count()


class TestSearchFunction(TestCase):
    def test_supports_session_queries(self):
        query = self.session.query(Order)
        assert (
            '''"order".search_vector @@ to_tsquery('english', :term)''' in
            str(search(query, 'something'))
        )


class TestSearchFilter(TestCase):
    def test_quotes_identifiers(self):
        query = self.session.query(Order)
        assert (
            search_filter(query, u'something') ==
            '''"order".search_vector @@ to_tsquery('english', :term)'''
        )


class TestSpecialCharacterSupport(TestCase):
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

    def test_supports_language_parameter(self):
        query = TextItemQuery(TextItem, self.session)
        query = query.search(u'orrimorri', language='finnish')
        assert "to_tsquery('finnish', :term)" in str(query)

    def test_single_quotes(self):
        query = TextItemQuery(TextItem, self.session)
        query = query.search(u"'orrimorri", language='finnish')
        assert query.count() == 1

    def test_double_quotes(self):
        query = TextItemQuery(TextItem, self.session)
        query = query.search(u'"orrimorri', language='finnish')
        assert query.count() == 1


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
