import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class TestClassConfiguration:
    @pytest.fixture
    def create_tables(self) -> None:
        pass

    def test_attaches_listener_only_once(
        self,
        Base: type[DeclarativeBase],
        engine: Engine,
    ) -> None:
        sa.orm.configure_mappers()

        class SomeClass(Base):  # type: ignore[valid-type, misc]
            __tablename__ = "some_class"
            id: Mapped[int] = mapped_column(primary_key=True)

        sa.orm.configure_mappers()

        Base.metadata.create_all(engine)
