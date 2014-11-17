from tests import TestCase


class SignedIntegerTokenTestCase(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.session.add(
            self.TextItem(name=u'index', content=u'some 12-14')
        )
        self.session.commit()


class TestSignedIntegersWithRemoveHyphens(SignedIntegerTokenTestCase):
    remove_symbols = '-@.'

    def test_with_hyphen_search_term(self):
        assert self.TextItemQuery(
            self.TextItem, self.session
        ).search('12-14').count()


class TestSignedIntegersWithoutRemoveHyphens(SignedIntegerTokenTestCase):
    remove_symbols = ''

    def test_with_hyphen_search_term(self):
        assert not self.TextItemQuery(
            self.TextItem, self.session
        ).search('12-14').count()
