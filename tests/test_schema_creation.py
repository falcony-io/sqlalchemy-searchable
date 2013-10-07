from tests import SchemaTestCase


class TestAutomaticallyCreatedSchemaItems(SchemaTestCase):
    should_create_indexes = [
        u'textitem_search_vector_index',
    ]
    should_create_triggers = [
        u'textitem_search_vector_trigger',
    ]
