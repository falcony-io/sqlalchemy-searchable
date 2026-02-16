from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sqlalchemy_searchable import search


class TestSearch:
    @pytest.fixture(
        params=[
            "{table}_{column}_trigger",
            "{table}_{column}_trg",
        ]
    )
    def search_trigger_name(self, request: pytest.FixtureRequest) -> Any:
        return request.param

    @pytest.fixture(
        params=[
            "{table}_{column}_update_trigger",
            "{table}_{column}_update",
        ]
    )
    def search_trigger_function_name(self, request: pytest.FixtureRequest) -> Any:
        return request.param

    @pytest.fixture(autouse=True)
    def items(self, session: Session, TextItem: type[Any]) -> list[Any]:
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

    def test_searches_through_all_fulltext_indexed_fields(
        self, TextItem: type[Any], session: Session
    ) -> None:
        query = search(select(TextItem), "admin")
        assert session.scalar(select(func.count()).select_from(query.subquery())) == 1

    def test_search_supports_term_splitting(
        self, TextItem: type[Any], session: Session
    ) -> None:
        query = search(select(TextItem), "content")
        assert session.scalar(select(func.count()).select_from(query.subquery())) == 3

    def test_term_splitting_supports_multiple_spaces(
        self, TextItem: type[Any], session: Session
    ) -> None:
        query = search(select(TextItem), "content  some").limit(1)
        assert session.scalars(query).one().name == "index"
        query = search(select(TextItem), "content   some").limit(1)
        assert session.scalars(query).one().name == "index"
        query = search(select(TextItem), "  ")
        assert session.scalar(select(func.count()).select_from(query.subquery())) == 4

    def test_search_by_email(self, TextItem: type[Any], session: Session) -> None:
        query = search(select(TextItem), "someone@example.com")
        assert (
            session.scalars(select(func.count()).select_from(query.subquery())).one()
            > 0
        )

    def test_supports_regconfig_parameter(
        self, TextItem: type[Any], session: Session
    ) -> None:
        query = search(select(TextItem), "orrimorri", regconfig="finnish")
        assert "parse_websearch(%(parse_websearch_1)s, %(parse_websearch_2)s)" in str(
            query.compile(session.bind)
        )

    def test_supports_vector_parameter(
        self, TextItem: type[Any], session: Session
    ) -> None:
        vector = TextItem.content_search_vector
        query = search(select(TextItem), "content", vector=vector)
        assert session.scalar(select(func.count()).select_from(query.subquery())) == 2

    def test_search_specific_columns(
        self, TextItem: type[Any], session: Session
    ) -> None:
        query = search(select(TextItem.id), "admin").subquery()
        assert session.scalar(select(func.count()).select_from(query)) == 1

    def test_sorted_search_results(
        self, TextItem: type[Any], session: Session, items: list[Any]
    ) -> None:
        query = search(select(TextItem), "some content", sort=True)
        sorted_results = session.scalars(query).all()
        assert sorted_results == items[0:2] + [items[3]]


class TestUsesGlobalConfigOptionsAsFallbacks:
    @pytest.fixture
    def search_manager_regconfig(self) -> str:
        return "pg_catalog.simple"

    @pytest.fixture(autouse=True)
    def items(self, session: Session, TextItem: type[Any]) -> None:
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

    def test_uses_global_regconfig_as_fallback(
        self, session: Session, TextItem: type[Any]
    ) -> None:
        query = search(select(TextItem.id), "the").subquery()
        assert session.scalar(select(func.count()).select_from(query)) == 1


class TestSearchableInheritance:
    @pytest.fixture(autouse=True)
    def articles(self, session: Session, Article: type[Any]) -> None:
        session.add(Article(name="index", content="some content"))
        session.add(Article(name="admin", content="admin content"))
        session.add(Article(name="home", content="this is the home page"))
        session.commit()

    def test_supports_inheritance(self, session: Session, Article: type[Any]) -> None:
        query = search(select(Article), "content")
        assert session.scalar(select(func.count()).select_from(query.subquery())) == 2
