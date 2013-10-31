from collections import defaultdict
from functools import partial

import six
import sqlalchemy as sa
from sqlalchemy_utils import TSVectorType
from sqlalchemy_utils.functions import has_changed
from sqlalchemy_utils.expressions import tsvector_concat


class CompositeTSVectorType(sa.types.TypeDecorator):
    impl = TSVectorType

    def __init__(self, attr_paths):
        self.attr_paths = attr_paths
        sa.types.TypeDecorator.__init__(self)


def search_vectors(obj):
    for property_ in sa.inspect(obj.__class__).iterate_properties:
        if (
            isinstance(property_, sa.orm.ColumnProperty) and
            isinstance(property_.columns[0].type, TSVectorType)
        ):
            yield property_.columns[0]


def has_changed_search_vector(obj):
    """
    Returns whether or not the search vector columns of given SQLAlchemy
    declarative object have changed.

    :param obj: SQLAlchemy declarative model object
    """
    for vector in search_vectors(obj):
        for column_name in vector.type.columns:
            if has_changed(obj, column_name):
                return True
    return False


def vector_agg(vector):
    return sa.sql.expression.cast(
        sa.func.coalesce(
            sa.func.array_to_string(sa.func.array_agg(vector), ' ')
        ),
        TSVectorType
    )


def parse_path(mapper, path):
    parts = path.split('.')

    if len(parts) == 1:
        if parts[0] not in mapper.columns:
            raise Exception()

        return mapper.columns[parts[0]]
    else:
        if parts[0] not in mapper.relationships:
            raise Exception()

        relationship = mapper.relationships[parts[0]]

        return relationship, parse_path(relationship.mapper, parts[1])


def configure_composite_search_vectors(mapper, class_):
    for column in class_.__table__.c:
        if isinstance(column.type, CompositeTSVectorType):
            register_listener(class_, column)


def register_listener(class_, column):
    attr_paths = column.type.attr_paths
    mapper = class_.__mapper__
    paths = map(partial(parse_path, mapper), attr_paths)

    def update_composite_search_vectors(session, flush_context):
        id_dict = defaultdict(list)
        joins = []
        vectors = []
        ids = []

        for obj in session:
            for path in paths:
                if isinstance(path, tuple):
                    if obj.__mapper__ == path[0].mapper:
                        id_dict[path[0]].append(obj.id)

                        if path[0] not in joins:
                            joins.append(getattr(class_, path[0].key))
                            vectors.append(path[1])
                else:
                    if isinstance(obj, class_):
                        if has_changed_search_vector(obj):
                            ids.append(obj.id)

        conditions = [class_.id.in_(ids)]

        for relation, ids in six.iteritems(id_dict):
            if relation.direction.name == 'MANYTOONE':
                conditions.append(
                    getattr(
                        class_,
                        relation.local_remote_pairs[0][0].name
                    ).in_(ids)
                )
            else:
                assert 0

        print map(str, conditions)

        alias = sa.orm.aliased(class_.__table__)

        query = session.query(
            alias.c.id,
            tsvector_concat(
                alias.c.search_vector,
                *map(vector_agg, vectors)
            ).label('combined_search_vector')
        )
        for join in joins:
            query = query.join(join)

        combined_search_vectors = (
            query
            .group_by(alias.c.id)
            .filter(sa.or_(class_.__table__.c.id == alias.c.id))
        ).correlate(class_.__table__)

        select = sa.select(
            [sa.literal_column('combined_search_vector')],
            from_obj=sa.alias(
                combined_search_vectors.statement,
                'combined_search_vectors'
            )
        )

        (
            session.query(class_)
            .filter(sa.or_(*conditions))
            .update(
                values={column.name: select},
                synchronize_session='fetch'
            )
        )

    sa.event.listen(
        sa.orm.session.Session,
        'after_flush',
        update_composite_search_vectors
    )


sa.event.listen(
    sa.orm.mapper,
    'mapper_configured',
    configure_composite_search_vectors
)
