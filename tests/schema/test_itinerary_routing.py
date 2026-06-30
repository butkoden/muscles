from muscles.core.schema.itinerary import Itinerary


class RouteRuleDefault:
    name = 'default'

    def is_match(self, value, chunk):
        return value == chunk

    def compile(self, value):
        return str(value)


class RouteRuleVar:
    name = 'var'

    def is_match(self, value, chunk):
        return chunk == '{id:var}' and value != ''

    def compile(self, value):
        return str(value)


class Request:
    def __init__(self, path, method='GET', content_type='text/plain'):
        self.path = path
        self.method = method
        self.content_type = content_type


def handler(**kwargs):
    return kwargs


def other_handler(**kwargs):
    return kwargs


def make_itinerary(name):
    itinerary = Itinerary(name=name)
    itinerary.add_rule(RouteRuleDefault())
    itinerary.add_rule(RouteRuleVar())
    return itinerary


def test_static_route_wins_over_dynamic_route():
    itinerary = make_itinerary('test-static-wins')
    dynamic_handler = itinerary.add('/items/{id}', key='items.show', handler=handler, method='GET')
    static_handler = itinerary.add('/items/new', key='items.new', handler=other_handler, method='GET')

    route, params = itinerary.get_current_route(Request('/items/new'))

    assert route['handler'] is static_handler
    assert route['handler'] is not dynamic_handler
    assert params == {}


def test_route_lookup_uses_key_index_and_params():
    itinerary = make_itinerary('test-key-index')
    registered = itinerary.add('/items/{id}', key='items.show', handler=handler, method='GET')
    itinerary.add('/items/{id}', key='items.show', handler=handler, method='POST')

    route, params = itinerary.get_current_route(Request('/items/42', method='GET'))

    assert route['handler'] is registered
    assert route['key'] == 'items.show'
    assert params == {'id': '42'}


def test_same_path_can_use_distinct_keys_per_method():
    itinerary = make_itinerary('test-path-method-distinct-keys')
    list_handler = itinerary.add('/items', key='items.list', handler=handler, method='GET')
    create_handler = itinerary.add('/items', key='items.create', handler=other_handler, method='POST')

    get_route, _ = itinerary.get_current_route(Request('/items', method='GET'))
    post_route, _ = itinerary.get_current_route(Request('/items', method='POST'))

    assert get_route['handler'] is list_handler
    assert get_route['key'] == 'items.list'
    assert post_route['handler'] is create_handler
    assert post_route['key'] == 'items.create'


def test_duplicate_route_registration_is_idempotent():
    itinerary = make_itinerary('test-duplicate-route')
    itinerary.add('/items/{id}', key='items.show', handler=handler, method='GET')
    routes_before = list(itinerary._routes_by_key['items.show'])

    itinerary.add('/items/{id}', key='items.show', handler=handler, method='GET')

    assert itinerary._routes_by_key['items.show'] == routes_before
    assert len(itinerary.nodes_map) == 1


def test_match_cache_is_cleared_when_route_is_added():
    itinerary = make_itinerary('test-cache-clear')

    assert itinerary.match('/late') is None
    assert itinerary._match_cache['/late'] is False

    itinerary.add('/late', key='late', handler=handler, method='GET')

    assert itinerary.match('/late').key == 'late'


def test_to_url_uses_indexed_route_records():
    itinerary = make_itinerary('test-to-url')
    itinerary.add('/items/{id}', key='items.show', handler=handler, method='GET')

    assert itinerary.to_url('items.show', {'id': 42}) == 'items/42'
