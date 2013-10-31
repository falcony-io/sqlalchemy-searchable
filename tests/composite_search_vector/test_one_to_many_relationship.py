import sqlalchemy as sa
from sqlalchemy_utils import TSVectorType
from sqlalchemy_searchable import CompositeTSVectorType
from tests import TestCase


class TestCompositeVectorWithManyToOneRelationship(TestCase):
    should_create_indexes = [
        u'textitem_search_vector_index',
    ]
    should_create_triggers = []

    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.Unicode(255))

            search_vector = sa.Column(TSVectorType('name', 'content'))

            fat_search_vector = sa.Column(
                CompositeTSVectorType([
                    'search_vector',
                    'tags.search_vector'
                ])
            )

            content = sa.Column(sa.UnicodeText)

        class Tag(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.Unicode(255))

            search_vector = sa.Column(TSVectorType('name'))

            article_id = sa.Column(sa.Integer, sa.ForeignKey(Article.id))

            article = sa.orm.relationship(Article, backref='tags')

        self.Article = Article
        self.Tag = Tag

    def test_updates_on_relationship_insert(self):
        article = self.Article(
            name=u'Some item',
            tags=[self.Tag(name=u'Great'), self.Tag(name=u'Bad')]
        )
        self.session.add(article)
        self.session.commit()

        assert 'item' in article.fat_search_vector
        assert 'great' in article.fat_search_vector
        assert 'bad' in article.fat_search_vector
