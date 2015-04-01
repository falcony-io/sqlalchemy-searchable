import sqlalchemy as sa

from tests import TestCase


class TestClassConfiguration(TestCase):
    def create_tables(self):
        pass

    def test_attaches_listener_only_once(self):
        sa.orm.configure_mappers()

        class SomeClass(self.Base):
            __tablename__ = 'some_class'
            id = sa.Column(sa.Integer, primary_key=True)

        sa.orm.configure_mappers()

        self.Base.metadata.create_all(self.engine)
