"""
Search query parser

Influenced by http://pyparsing.wikispaces.com/file/view/searchparser.py
"""
import re
import unicodedata

import six
from pyparsing import (
    Forward,
    Group,
    Keyword,
    Literal,
    OneOrMore,
    Suppress,
    Word
)
from validators import email


def is_alphanumeric(c):
    return unicodedata.category(c) in ['Lu', 'Ll', 'Nd']


all_unicode = u''.join(six.unichr(c) for c in six.moves.range(65536))
unicode_alnum = ''.join(
    c for c in all_unicode
    if is_alphanumeric(c)
)
unicode_non_alnum = ''.join(
    c for c in all_unicode
    if not is_alphanumeric(c) and
    c not in ['-', '(', ')']
)


class SearchQueryParser(object):
    def __init__(self, wildcard=':*', emails_as_tokens=False):
        self.wildcard = wildcard
        self.emails_as_tokens = emails_as_tokens
        self._methods = {
            'and': self.eval_and,
            'not': self.eval_not,
            'or': self.eval_or,
            'parenthesis': self.eval_parenthesis,
            'word': self.eval_word
        }
        self._parser = self.parser()

    def remove_special_chars(self, term):
        """
        Removes all illegal characters from the search term. PostgreSQL search
        vector parser notices email addresses hence we need special parsing for
        them.

        :param term: search term to filter
        """
        if self.emails_as_tokens and email(term):
            return term
        else:
            return re.sub(r'[%s]+' % unicode_non_alnum, ' ', term)

    def parser(self):
        """
        This function returns a grammar for parsing postgresql full text search
        queries.

        Grammar:
        - a query consists of alphanumeric words
        - words can be used together by using operators ('and' or 'or')
        - words with operators can be grouped with parenthesis
        - a word or group of words can be preceded by a 'not' operator
        - the 'and' operator precedes an 'or' operator
        - if an operator is missing, use an 'and' operator
        """
        or_ = Forward()

        word = Group(Word(unicode_alnum + '@.')).setResultsName('word')

        parenthesis = Group(
            (Suppress('(') + or_ + Suppress(')'))
        ).setResultsName('parenthesis') | word

        not_ = Forward()
        not_ <<= (Group(
            Suppress(Literal('-')) + not_
        ).setResultsName('not') | parenthesis)

        keyword_or = Keyword('or', caseless=True)

        and_ = Forward()

        and_ <<= (
            Group(
                not_ +
                OneOrMore(Suppress(Keyword(' '))) +
                and_
            ).setResultsName('and') |
            Group(
                not_ +
                OneOrMore(
                    ~keyword_or + and_
                )
            ).setResultsName('and') |
            not_
        )

        or_ <<= (
            Group(
                and_ + OneOrMore(Suppress(keyword_or)) + or_
            ).setResultsName('or') |
            and_
        )

        return or_.parseString

    def eval_and(self, argument):
        return '%s & %s' % (
            self.evaluate(argument[0]),
            self.evaluate(argument[1])
        )

    def eval_or(self, argument):
        return '%s | %s' % (
            self.evaluate(argument[0]),
            self.evaluate(argument[1])
        )

    def eval_not(self, argument):
        return '! %s' % self.evaluate(argument[0])

    def eval_parenthesis(self, argument):
        if argument[0].getName() == 'parenthesis':
            return self.evaluate(argument[0])
        return '(%s)' % self.evaluate(argument[0])

    def eval_word(self, argument):
        return '%s%s' % (argument[0], self.wildcard)

    def evaluate(self, argument):
        return self._methods[argument.getName()](argument)

    def parse(self, query):
        return self.evaluate(self._parser(query)[0])
