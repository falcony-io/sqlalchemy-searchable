Alembic migrations
------------------

When making changes to your database schema you have to make sure the associated search triggers and trigger functions get updated also. SQLAlchemy-Searchable offers a helper function called `sync_trigger` for this.


.. module:: sqlalchemy_searchable
.. autofunction:: sync_trigger
