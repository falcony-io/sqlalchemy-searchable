import sqlalchemy as sa
from sqlalchemy_utils import TSVectorType

from sqlalchemy_searchable.composite import CompositeSearch
from tests import create_test_cases, TestCase


class CompositeSearchTestCase(TestCase):
    def create_models(self):
        TestCase.create_models(self)

        class Blog(self.Base):
            __tablename__ = 'blog'

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name1 = sa.Column(sa.Unicode(255))
            content1 = sa.Column(sa.UnicodeText)
            search_vector = sa.Column(TSVectorType('name1', 'content1'))

        self.Blog = Blog

        class User(self.Base):
            __tablename__ = 'user'

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name2 = sa.Column(sa.Unicode(255))
            content2 = sa.Column(sa.UnicodeText)
            search_vector = sa.Column(TSVectorType('name2', 'content2'))

        self.User = User

    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.session.add(
            self.Blog(name1=u'ipsum', content1=u'admin content')
        )
        self.session.add(
            self.User(name2=u'index', content2=u'lorem ipsum')
        )
        self.session.commit()

    def test_composite_search(self):
        s = CompositeSearch(self.session, [self.User, self.Blog])

        result = s.search(query=s.build_query('ipsum'))

        assert len(result) == 2
        user = [x for x in result if x['type'] == 'User'][0]['content']
        blog = [x for x in result if x['type'] == 'Blog'][0]['content']
        assert isinstance(user, self.User)
        assert isinstance(blog, self.Blog)

        result = s.search(query=s.build_query('admin'))

        assert len(result) == 1
        assert result[0]['type'] == 'Blog'
        assert isinstance(result[0]['content'], self.Blog)

        result = s.search(query=s.build_query('lorem'))

        assert len(result) == 1
        assert result[0]['type'] == 'User'
        assert isinstance(result[0]['content'], self.User)

        result = s.search(query=s.build_query('stars'))

        assert len(result) == 0


create_test_cases(CompositeSearchTestCase)
