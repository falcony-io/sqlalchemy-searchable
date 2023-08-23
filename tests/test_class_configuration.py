import pytest
import sqlalchemy as sa


class TestClassConfiguration:
    @pytest.fixture
    def create_tables(self):
        pass

    def test_attaches_listener_only_once(self, Base, engine):
        sa.orm.configure_mappers()

        class SomeClass(Base):
            __tablename__ = "some_class"
            id = sa.Column(sa.Integer, primary_key=True)

        sa.orm.configure_mappers()

        Base.metadata.create_all(engine)
