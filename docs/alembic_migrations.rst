Alembic migrations
------------------

.. currentmodule:: sqlalchemy_searchable

When making changes to your database schema, you have to ensure the associated
search triggers and trigger functions get updated also. SQLAlchemy-Searchable
offers two helper functions for this: :func:`sync_trigger` and
:func:`drop_trigger`.

.. autofunction:: sync_trigger
.. autofunction:: drop_trigger
