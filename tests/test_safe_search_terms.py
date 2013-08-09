from sqlalchemy_searchable import safe_search_terms


class TestSafeSearchTerms(object):
    def test_uses_pgsql_wildcard_by_default(self):
        assert safe_search_terms('star wars') == [
            'star:*', 'wars:*'
        ]

    def test_escapes_special_chars(self):
        assert safe_search_terms('star!#') == [
            'star:*'
        ]

    def test_supports_custom_wildcards(self):
        assert safe_search_terms('star wars', wildcard='*') == [
            'star*', 'wars*'
        ]
