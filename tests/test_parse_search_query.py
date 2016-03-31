# -*- coding: utf-8 -*-
from sqlalchemy_searchable import parse_search_query
from sqlalchemy_searchable.parser import SearchQueryParser


class TestParseSearchQuery(object):
    def test_uses_pgsql_wildcard_by_default(self):
        assert parse_search_query('star wars') == 'star:* & wars:*'

    def test_escapes_special_chars(self):
        assert parse_search_query('star!#') == 'star:*'

    def test_supports_custom_parsers(self):
        assert (
            parse_search_query(
                'star wars',
                parser=SearchQueryParser(wildcard='*')
            ) == 'star* & wars*'
        )

    def test_operator_parsing(self):
        assert (
            parse_search_query('star or wars') ==
            'star:* | wars:*'
        )

    def test_empty_string(self):
        parse_search_query('') == ''

    def test_numbers(self):
        assert (
            parse_search_query('12331 or 12a12') ==
            '12331:* | 12a12:*'
        )

    def test_emails_without_email_tokens(self):
        assert (
            parse_search_query('john@fastmonkeys.com') ==
            'john:* & fastmonkeys:* & com:*'
        )

    def test_emails_with_email_tokens(self):
        assert (
            parse_search_query(
                'john@fastmonkeys.com',
                parser=SearchQueryParser(emails_as_tokens=True)
            ) ==
            'john@fastmonkeys.com:*'
        )

    def test_hyphen_between_words(self):
        assert parse_search_query('star-wars') == 'star:* & wars:*'

    def test_or(self):
        assert parse_search_query('star or wars') == 'star:* | wars:*'

    def test_multiple_ors(self):
        assert parse_search_query('star or or or wars') == 'star:* | wars:*'

    def test_space_as_and(self):
        assert parse_search_query('star wars') == 'star:* & wars:*'

    def test_multiple_spaces_as_and(self):
        assert (
            parse_search_query('star   wars    luke') ==
            'star:* & wars:* & luke:*'
        )

    def test_and(self):
        assert parse_search_query('star wars') == 'star:* & wars:*'

    def test_parenthesis(self):
        assert parse_search_query('(star wars) or luke') == (
            '(star:* & wars:*) | luke:*'
        )

    def test_or_and(self):
        assert (
            parse_search_query('star or wars luke or solo') ==
            'star:* | wars:* & luke:* | solo:*'
        )

    def test_empty_parenthesis(self):
        assert parse_search_query('()') == ''

    def test_nested_parenthesis(self):
        assert parse_search_query('((star wars)) or luke') == (
            '(star:* & wars:*) | luke:*'
        )

    def test_not(self):
        assert parse_search_query('-star') == (
            '! star:*'
        )

    def test_not_between_words(self):
        assert parse_search_query('wars -star') == (
            'wars:* & ! star:*'
        )
        assert parse_search_query(u'äää -ööö') == (
            u'äää:* & ! ööö:*'
        )

    def test_not_with_parenthesis(self):
        assert parse_search_query('-(star wars)') == '! (star:* & wars:*)'

    def test_double_quotes(self):
        assert parse_search_query('"star') == (
            'star:*'
        )

    def test_search_supports_non_english_characters(self):
        parse_search_query(u'ähtäri') == (
            u'ähtäri:*'
        )

    def test_special_chars(self):
        assert parse_search_query("star!:*@@?`") == (
            'star:*'
        )

    def test_single_quotes(self):
        assert parse_search_query("'star'") == (
            'star:*'
        )

    def test_or_within_a_token(self):
        assert parse_search_query('organs') == (
            'organs:*'
        )

    def test_or_within_a_token_preceded_by_space(self):
        assert parse_search_query('star organs') == (
            'star:* & organs:*'
        )

    def test_and_within_a_token_preceded_by_space(self):
        assert parse_search_query('star andromeda') == (
            'star:* & andromeda:*'
        )
