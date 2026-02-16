from collections.abc import Callable
from functools import wraps
from inspect import isclass
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.type_api import TypeEngine

VectorizerFunc = Callable[[sa.ColumnClause[Any]], sa.ColumnElement[str]]


class Vectorizer:
    def __init__(
        self,
        type_vectorizers: dict[type[TypeEngine[Any]], VectorizerFunc] | None = None,
        column_vectorizers: dict[sa.Column[Any], VectorizerFunc] | None = None,
    ):
        self.type_vectorizers = {} if type_vectorizers is None else type_vectorizers
        self.column_vectorizers = (
            {} if column_vectorizers is None else column_vectorizers
        )

    def clear(self) -> None:
        """Clear all registered vectorizers."""
        self.type_vectorizers = {}
        self.column_vectorizers = {}

    def contains_tsvector(self, tsvector_column: sa.Column[Any]) -> bool:
        if not hasattr(tsvector_column.type, "columns"):
            return False
        return any(
            getattr(tsvector_column.table.c, column) in self
            for column in tsvector_column.type.columns
        )

    def __contains__(self, column: sa.Column[Any]) -> bool:
        try:
            self[column]
            return True
        except KeyError:
            return False

    def __getitem__(self, column: sa.Column[Any]) -> VectorizerFunc:
        if column in self.column_vectorizers:
            return self.column_vectorizers[column]
        type_class = column.type.__class__

        if type_class in self.type_vectorizers:
            return self.type_vectorizers[type_class]
        raise KeyError(column)

    def __call__(
        self,
        type_or_column: type[TypeEngine[Any]]
        | sa.Column[Any]
        | InstrumentedAttribute[Any],
    ) -> Callable[[VectorizerFunc], VectorizerFunc]:
        """Decorator to register a function as a vectorizer.

        :param type_or_column: the SQLAlchemy database data type or the column to
            register a vectorizer for
        """

        def outer(func: VectorizerFunc) -> VectorizerFunc:
            @wraps(func)
            def wrapper(
                column_reference: sa.ColumnClause[Any],
            ) -> sa.ColumnElement[str]:
                return func(column_reference)

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
