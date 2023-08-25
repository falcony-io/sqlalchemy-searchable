from functools import wraps
from inspect import isclass

import sqlalchemy as sa
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.type_api import TypeEngine


class Vectorizer:
    def __init__(self, type_vectorizers=None, column_vectorizers=None):
        self.type_vectorizers = {} if type_vectorizers is None else type_vectorizers
        self.column_vectorizers = (
            {} if column_vectorizers is None else column_vectorizers
        )

    def clear(self):
        """Clear all registered vectorizers."""
        self.type_vectorizers = {}
        self.column_vectorizers = {}

    def contains_tsvector(self, tsvector_column):
        if not hasattr(tsvector_column.type, "columns"):
            return False
        return any(
            getattr(tsvector_column.table.c, column) in self
            for column in tsvector_column.type.columns
        )

    def __contains__(self, column):
        try:
            self[column]
            return True
        except KeyError:
            return False

    def __getitem__(self, column):
        if column in self.column_vectorizers:
            return self.column_vectorizers[column]
        type_class = column.type.__class__

        if type_class in self.type_vectorizers:
            return self.type_vectorizers[type_class]
        raise KeyError(column)

    def __call__(self, type_or_column):
        """Decorator to register a function as a vectorizer.

        :param type_or_column: the SQLAlchemy database data type or the column to
            register a vectorizer for
        """

        def outer(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            if isclass(type_or_column) and issubclass(type_or_column, TypeEngine):
                self.type_vectorizers[type_or_column] = wrapper
            elif isinstance(type_or_column, sa.Column):
                self.column_vectorizers[type_or_column] = wrapper
            elif isinstance(type_or_column, InstrumentedAttribute):
                prop = type_or_column.property
                if not isinstance(prop, sa.orm.ColumnProperty):
                    raise TypeError(
                        "Given InstrumentedAttribute does not wrap "
                        "ColumnProperty. Only instances of ColumnProperty are "
                        "supported for vectorizer."
                    )
                column = type_or_column.property.columns[0]

                self.column_vectorizers[column] = wrapper
            else:
                raise TypeError(
                    "First argument should be either valid SQLAlchemy type, "
                    "Column, ColumnProperty or InstrumentedAttribute object."
                )

            return wrapper

        return outer
