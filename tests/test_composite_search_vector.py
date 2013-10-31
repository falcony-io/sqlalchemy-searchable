import sqlalchemy as sa
from sqlalchemy_utils import TSVectorType
from sqlalchemy_searchable import CompositeTSVectorType
from tests import TestCase


class TestCompositeSearchVector(TestCase):
    should_create_indexes = [
        u'textitem_search_vector_index',
    ]
    should_create_triggers = []

    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.Unicode(255))

            search_vector = sa.Column(TSVectorType('name'))

        class TextItem(self.Base):
            __tablename__ = 'textitem'

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.Unicode(255))

            search_vector = sa.Column(TSVectorType('name', 'content'))

            fat_search_vector = sa.Column(
                CompositeTSVectorType([
                    'search_vector',
                    'author.search_vector'
                ])
            )

            content = sa.Column(sa.UnicodeText)

            author_id = sa.Column(sa.Integer, sa.ForeignKey(User.id))

            author = sa.orm.relationship(User, backref='items')

        self.TextItem = TextItem
        self.User = User

    def test_updates_on_insert(self):
        item = self.TextItem(name=u'Some item')
        self.session.add(item)
        self.session.commit()

        assert item.fat_search_vector == item.search_vector

    def test_updates_on_relationship_insert(self):
        item = self.TextItem(
            name=u'Some item',
            author=self.User(name=u'John Matrix')
        )
        self.session.add(item)
        self.session.commit()

        assert 'item' in item.fat_search_vector
        assert 'john' in item.fat_search_vector
        assert 'matrix' in item.fat_search_vector
