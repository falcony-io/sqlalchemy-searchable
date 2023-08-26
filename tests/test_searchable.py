import pytest
from sqlalchemy import func, select
from sqlalchemy.orm.query import Query

from sqlalchemy_searchable import search, SearchQueryMixin


class TextItemQuery(Query, SearchQueryMixin):
    pass


class TestSearchQueryMixin:
    @pytest.fixture(
        params=[
            "{table}_{column}_trigger",
            "{table}_{column}_trg",
        ]
    )
    def search_trigger_name(self, request):
        return request.param

    @pytest.fixture(
        params=[
            "{table}_{column}_update_trigger",
            "{table}_{column}_update",
        ]
    )
    def search_trigger_function_name(self, request):
        return request.param

    @pytest.fixture(autouse=True)
    def items(self, session, TextItem):
        items = [
            TextItem(name="index", content="some content"),
            TextItem(name="admin", content="admin content"),
            TextItem(
                name="home", content="this is the home page of someone@example.com"
            ),
            TextItem(name="not a some content", content="not a name"),
        ]
        session.add_all(items)
        session.commit()
        return items

    def test_searches_through_all_fulltext_indexed_fields(self, TextItem, session):
        assert TextItemQuery(TextItem, session).search("admin").count() == 1

    def test_search_supports_term_splitting(self, TextItem, session):
        assert TextItemQuery(TextItem, session).search("content").count() == 3

    def test_term_splitting_supports_multiple_spaces(self, TextItem, session):
        query = TextItemQuery(TextItem, session)
        assert query.search("content  some").first().name == "index"
        assert query.search("content   some").first().name == "index"
        assert query.search("  ").count() == 4

    def test_search_by_email(self, TextItem, session):
        assert TextItemQuery(TextItem, session).search("someone@example.com").count()

    def test_supports_regconfig_parameter(self, TextItem, session):
        query = TextItemQuery(TextItem, session)
        query = query.search("orrimorri", regconfig="finnish")
        assert "parse_websearch(%(parse_websearch_1)s, %(parse_websearch_2)s)" in str(
            query.statement.compile(session.bind)
        )

    def test_supports_vector_parameter(self, TextItem, session):
        vector = TextItem.content_search_vector
        query = TextItemQuery(TextItem, session)
        query = query.search("content", vector=vector)
        assert query.count() == 2

    def test_search_specific_columns(self, TextItem, session):
        query = search(select(TextItem.id), "admin").subquery()
        assert session.scalar(select(func.count()).select_from(query)) == 1

    def test_sorted_search_results(self, TextItem, session, items):
        query = TextItemQuery(TextItem, session)
        sorted_results = query.search("some content", sort=True).all()
        assert sorted_results == items[0:2] + [items[3]]


class TestUsesGlobalConfigOptionsAsFallbacks:
    @pytest.fixture
    def search_manager_regconfig(self):
        return "pg_catalog.simple"

    @pytest.fixture(autouse=True)
    def items(self, session, TextItem):
        items = [
            TextItem(name="index", content="some content"),
            TextItem(name="admin", content="admin content"),
            TextItem(
                name="home", content="this is the home page of someone@example.com"
            ),
            TextItem(name="not a some content", content="not a name"),
        ]
        session.add_all(items)
        session.commit()

    def test_uses_global_regconfig_as_fallback(self, session, TextItem):
        query = search(select(TextItem.id), "the").subquery()
        assert session.scalar(select(func.count()).select_from(query)) == 1


class TestSearchableInheritance:
    @pytest.fixture(autouse=True)
    def articles(self, session, Article):
        session.add(Article(name="index", content="some content"))
        session.add(Article(name="admin", content="admin content"))
        session.add(Article(name="home", content="this is the home page"))
        session.commit()

    def test_supports_inheritance(self, session, Article):
        assert TextItemQuery(Article, session).search("content").count() == 2
