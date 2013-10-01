"""
Search query parser

Influenced by http://pyparsing.wikispaces.com/file/view/searchparser.py
"""
import unicodedata

from pyparsing import (
    Forward,
    Group,
    Keyword,
    Literal,
    oneOf,
    OneOrMore,
    Suppress,
    Word,
)


all_unicode = u''.join(unichr(c) for c in xrange(65536))
unicode_letters = ''.join(
    c for c in all_unicode
    if unicodedata.category(c) == 'Lu' or unicodedata.category(c) == 'Ll'
)
unicode_non_letters = ''.join(
    c for c in all_unicode
    if unicodedata.category(c) != 'Lu' and unicodedata.category(c) != 'Ll'
)


class SearchQueryParser(object):
    def __init__(self, wildcard=':*'):
        self.wildcard = wildcard
        self._methods = {
            'and': self.eval_and,
            'not': self.eval_not,
            'or': self.eval_or,
            'parenthesis': self.eval_parenthesis,
            'word': self.eval_word
        }
        self._parser = self.parser()

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

        word = Group(Word(unicode_letters)).setResultsName('word')

        parenthesis = Group(
            (Suppress('(') + or_ + Suppress(')'))
        ).setResultsName('parenthesis') | word

        not_ = Forward()
        not_ << (Group(
            Suppress(Literal('-')) + not_
        ).setResultsName('not') | parenthesis)

        and_ = Forward()
        and_ << (
            Group(
                not_ +
                OneOrMore(Suppress(Keyword('and', caseless=True))) +
                and_
            ).setResultsName('and') |
            Group(
                not_ +
                OneOrMore(~oneOf('and or') + and_)
            ).setResultsName('and') |
            not_
        )

        or_ << (
            Group(
                and_ + OneOrMore(Suppress(Keyword('or', caseless=True))) + or_
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
