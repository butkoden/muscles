import inspect
import logging
import re
import os
import typing
import traceback
from collections import defaultdict
from functools import wraps
from abc import ABC
from urllib.parse import unquote
from fnmatch import fnmatch

from ..exceptions import ApplicationException, AccessDeniedException
from ..route_contract import normalize_path
from .schema import Schema
from .security import BaseSecurity
from .user import GuestUser


RouteRecord = dict[str, typing.Any]
SecurityDeclaration = list[typing.Union[BaseSecurity, str]]


HTTP_METHOD_GET = 'get'
HTTP_METHOD_POST = 'post'
HTTP_METHOD_PUT = 'put'
HTTP_METHOD_DELETE = 'delete'
HTTP_METHOD_HEAR = 'head'
HTTP_METHOD_PATCH = 'patch'
HTTP_METHOD_OPTION = 'options'
HTTP_METHOD_TRACE = 'trace'
HTTP_METHOD_CONNECT = 'connect'


def _is_route_param(chunk: str) -> bool:
    return bool(chunk) and chunk[0] == '{' and chunk[-1] == '}'


def _parse_route_chunk(chunk: str):
    if _is_route_param(chunk):
        body = chunk[1:-1]
        name, sep, rule_name = body.partition(':')
        return f"{{{name}:{rule_name or 'var'}}}", name, (rule_name or "var"), True
    return chunk, False, "default", False


def _merge_metadata(parent_value, child_value):
    if child_value not in (None, [], {}, ""):
        if isinstance(parent_value, list) and isinstance(child_value, list):
            return [*parent_value, *[item for item in child_value if item not in parent_value]]
        if isinstance(parent_value, dict) and isinstance(child_value, dict):
            merged = dict(parent_value)
            merged.update(child_value)
            return merged
        return child_value
    return parent_value


def _path_matches(pattern: str, path: str) -> bool:
    pattern = normalize_path(pattern)
    path = normalize_path(path)
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(f"{prefix}/")
    return fnmatch(path, pattern)


def _route_path_key(route: str) -> str:
    return normalize_path(route).lower()


def _auth_security(auth):
    if auth is False or auth is None:
        return []
    if isinstance(auth, list):
        return auth
    return [auth]


class RouteGroup:
    def __init__(self, itinerary, prefix: str, **metadata):
        self.itinerary = itinerary
        self.prefix = normalize_path(prefix)
        self.metadata = metadata

    def _route(self, route: str) -> str:
        return normalize_path(self.prefix, route)

    def _kwargs(self, kwargs: dict) -> dict:
        merged = dict(kwargs)
        for key, value in self.metadata.items():
            merged[key] = _merge_metadata(value, merged.get(key))
        return merged

    def init(self, route, *args, **kwargs):
        return self.itinerary.init(self._route(route), *args, **self._kwargs(kwargs))

    def action(self, *args, route=None, **kwargs):
        return self.itinerary.action(*args, route=self._route(route or "/"), **self._kwargs(kwargs))

    def controller(self, route, *args, **kwargs):
        return self.itinerary.controller(self._route(route), *args, **self._kwargs(kwargs))

    def group(self, prefix: str, **metadata):
        merged = dict(self.metadata)
        for key, value in metadata.items():
            merged[key] = _merge_metadata(merged.get(key), value)
        return RouteGroup(self.itinerary, self._route(prefix), **merged)


class Itinerary:
    """
    Базовый класс для работы с роутами
    """

    legal_http_method: list[str] = [
        HTTP_METHOD_GET,
        HTTP_METHOD_POST,
        HTTP_METHOD_PUT,
        HTTP_METHOD_DELETE,
        HTTP_METHOD_HEAR,
        HTTP_METHOD_PATCH,
        HTTP_METHOD_OPTION,
        HTTP_METHOD_TRACE,
        HTTP_METHOD_CONNECT,
    ]
    

    # nodes_map = []
    # static_map = []
    error_handler_map: list[RouteRecord] = []
    rules: list[typing.Any] = []
    node: "Node"
    prefix: typing.Optional[str]
    nodes_map: list[RouteRecord]
    static_map: list[RouteRecord]
    _routes_by_key: typing.DefaultDict[str, list[RouteRecord]]
    _routes_by_path: typing.DefaultDict[str, list[RouteRecord]]
    _error_handlers_by_code: dict[typing.Any, typing.Callable[..., typing.Any]]
    _error_handlers_by_exception: dict[type[BaseException], typing.Callable[..., typing.Any]]
    _error_status_by_exception: dict[type[BaseException], int]
    _default_error_handler: typing.Optional[typing.Callable[..., typing.Any]]
    _match_cache: dict[str, typing.Union["Node", bool]]
    _middlewares: list[typing.Callable[..., typing.Any]]
    _guards: list[dict[str, typing.Any]]
    _events: dict[typing.Any, list[typing.Any]]
    install: bool
    _instances: dict[tuple[type, typing.Optional[str]], "Itinerary"] = {}

    set_response: dict[str, typing.Any] = {}

    def __new__(cls, *args, prefix=None, version=None, name=None, **kwargs):
        """
        Создает синглтон объект роутера, формирует первую ноду роутера
        :param args:
        :param prefix: префикс роутера
        :param version: Версия роутера
        :param name: Название роутера
        :param kwargs:
        """
        instance_name = (cls, name)
        if instance_name not in cls._instances:
            instance = typing.cast("Itinerary", super(Itinerary, cls).__new__(cls))
            instance.node = Node('')
            instance.prefix = prefix
            instance.nodes_map = []
            instance.static_map = []
            instance._routes_by_key = defaultdict(list)
            instance._routes_by_path = defaultdict(list)
            instance._error_handlers_by_code = {}
            instance._error_handlers_by_exception = {}
            instance._error_status_by_exception = {}
            instance._default_error_handler = None
            instance._match_cache = {}
            instance._middlewares = []
            instance._guards = []
            cls._instances[instance_name] = instance
        return cls._instances[instance_name]

    def __init__(self, *args, **kwargs):
        if not hasattr(self, '_events'):
            self._events = {}
        if not hasattr(self, 'install'):
            self.__before_init__(*args, **kwargs)
            self.install = True

    def __before_init__(self, *args, **kwargs):
        pass

    def add_event(self, key, value):
        """ Добавляет событие key в очередь событий """
        if key not in self._events:
            self._events.update({key: []})
        self._events[key].append(value)

    def get_event(self, key):
        """ Извлекает события key из очереди событий """
        if key not in self._events:
            return []
        return self._events[key]

    def instance_keys(self):
        """
        Получает ключи созданых роутеров

        :return: List(dict)
        """
        return self._instances.keys()

    def instance_list(self):
        """
        Получает список объектов роутеоров

        :return: List
        """
        return self._instances.items()

    def add_rule(self, rule):
        """
        Добавляет новое правило в доступный список правил

        :param rule: Объект правила
        :return:
        """
        if not any(item.name == rule.name for item in self.rules):
            self.rules.append(rule)

    def group(self, prefix: str, **metadata):
        return RouteGroup(self, prefix, **metadata)

    def use(self, middleware):
        self._middlewares.append(middleware)
        return middleware

    def get_middlewares(self):
        return list(self._middlewares)

    def guard(self, pattern: str, handler, except_: typing.Optional[list[str]] = None):
        self._guards.append({
            "pattern": pattern,
            "handler": handler,
            "except": except_ or [],
        })
        return handler

    def get_guards(self, request_or_path):
        path = request_or_path if isinstance(request_or_path, str) else getattr(request_or_path, "path", "/")
        route = None if isinstance(request_or_path, str) else getattr(request_or_path, "route", None)
        if self.is_auth_disabled(route):
            return []
        handlers = []
        for guard in self._guards:
            if not _path_matches(guard["pattern"], path):
                continue
            if any(_path_matches(pattern, path) for pattern in guard["except"]):
                continue
            handlers.append(guard["handler"])
        return handlers

    def is_auth_disabled(self, route_or_handler):
        if route_or_handler is None:
            return False
        handler = route_or_handler.get("handler") if isinstance(route_or_handler, dict) else route_or_handler
        return getattr(handler, "auth", None) is False

    def to_url(self, route_key, params):
        """
        Формирует из ключа маршрута и параметров ссылку

        :param route_key: Ключ маршрута
        :param params: Параметры
        :return:
        """
        l = []

        def repl(m: re.Match[str]) -> str:
            name = m.group(3) if m.group(3) else 'var'
            for rule in self.rules:
                if rule.name == name:
                    return str(rule.compile(params.get(m.group(2), '')))
            return str(params.get(m.group(2), ''))

        for r in self._routes_by_key.get(route_key, []):
            rs = r['route'].split('/')
            for s in rs:
                l.append(re.sub(r"(\{([\w\d\%\_\-]+)\:?([\w\d\%\_\-]+)?\})", repl, s))
            break
        return '/'.join(l)

    def match(self, url):
        """
        Находит подходящий маршрут по УРЛ

        :param url: Ссылка
        :return:
        """
        if url == '/':
            url = '/main'
        cached = self._match_cache.get(url)
        if cached is not None:
            return cached or None
        chunks = [chunk for chunk in url.split('/') if chunk]
        for route in self._match(self.node, chunks, 0):
            if route.key and route.key in self._routes_by_key:
                self._match_cache[url] = route
                return route
        self._match_cache[url] = False
        return None

    def _match(self, route, chunks, index=0):
        """
        Поиск подходящих узлов

        :param route:
        :param chunks:
        :param paths:
        :param n:
        :return:
        """
        if index >= len(chunks):
            return
        chunk = chunks[index]
        last_index = len(chunks) - 1
        for node in route.childrens:
            if node.is_match(chunk):
                if index == last_index:
                    yield node
                else:
                    yield from self._match(node, chunks, index + 1)

    def match_with_params(self, url):
        """
        Возвращает подходящий маршрут с параметрами

        :param url: УРЛ
        :return:
        """
        chunks = url.split('/')
        node = self.match(url)
        if not isinstance(node, Node):
            return None, {}
        _node: typing.Optional[Node] = node
        dictionary = {}
        for chunk in chunks[::-1]:
            if _node is None:
                break
            if _node.dictionary_key:
                dictionary.update(_node.dictionary(chunk))
            _node = _node.parent
        return node, dictionary

    def add_static(self, directory: str, prefix: typing.Optional[str] = None, handler=None, full_path: bool = False):
        """
        функции обработки статических файлов

        :param directory: Директория фалов
        :param prefix: Префик для маршрута
        :param handler: Обработчик маршрута
        :param bool full_path: Полуный путь маршрута
        :return:
        """
        for c in self.static_map:
            if directory == c['directory'] and prefix == c['prefix']:
                raise Exception('Route must have unique `prefix` [%s] and `route` [%s] values' % (prefix, directory))
        self.static_map.append({
            "directory": directory if full_path else os.path.join(os.getcwd(), directory),
            "prefix": prefix,
            'handler': handler,
        })

    def static(self, directory: str, prefix: typing.Optional[str] = None, full_path: bool = False):
        """
        Декторатор функции обработки статических файлов

        :param directory: Директория фалов
        :param prefix: Префик для маршрута
        :param bool full_path: Полуный путь маршрута
        :return:
        """

        def decorator(func):
            self.add_static(directory, prefix=prefix, handler=func, full_path=full_path)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper

        return decorator

    def get_current_static(self, request):
        """
        Возвращает обработчик статических файлов

        :param request: Объект запроса
        :return:
        """

        def condition(route):
            '''condition here'''
            res = True
            if res and route['prefix'] and not request.path.lower().startswith(route['prefix'] + '/'.lower()):
                res = False
            return res

        for static in self.static_map:
            if condition(static):
                return static
        return None

    def _trigger_set_handler(self, handler, *args, **kwargs):
        if "auth" in kwargs and kwargs["auth"] is not None:
            kwargs["security"] = _auth_security(kwargs["auth"])
        handler.is_action = kwargs.get('is_action', False)
        handler.key = kwargs.get('key')
        handler.module = kwargs.get('module')
        handler.method = kwargs.get('method')
        handler.content_type = kwargs.get('content_type')
        handler.redirect = kwargs.get('redirect')
        handler.route = kwargs.get('route', '/')
        handler.model = kwargs.get('model')
        for key, value in kwargs.items():
            if key.startswith("_"):
                continue
            if value in (None, [], {}, "") and hasattr(handler, key):
                continue
            setattr(handler, key, value)
        return handler

    def _trigger_set_controller(self, handler, *args, **kwargs):
        return handler

    def add(self, route: str, key: typing.Optional[str] = None, handler: typing.Any = None,
            method: typing.Optional[str] = None, content_type: typing.Optional[str] = None,
            redirect: typing.Optional[str] = None, module=None,
            canonical_route: typing.Optional[str] = None, aliases: typing.Optional[list[str]] = None):
        """
        Добавляет функцию обработки маршрута

        :param route: Маршрут
        :param key: Ключь маршрута
        :param handler: Обработчик маршрута
        :param method: Метод маршрута
        :param content_type: Тип контента маршрута
        :param redirect: Редирект для маршрута
        :param module: Настройки модуля обработки
        :return:
        """

        if route == '/':
            route = '/main'
        if module is not None and 'url_prefix' in module:
            route = '/'.join(module['url_prefix'].split('/') + route.split('/'))
        full_route = route
        full_route = '/'.join([i for i in full_route.split('/') if i != ''])
        if not full_route.startswith('/'):
            full_route = "/%s" % full_route

        if self.prefix:
            route = '/'.join(self.prefix.split('/') + route.split('/'))

        route = '/'.join([i for i in route.split('/') if i != ''])

        if handler is None:
            raise Exception('The `handler` parameter is mandatory')

        chunks = route.split('/')
        self._match_cache.clear()
        node = self.node
        canonical_route = canonical_route if canonical_route is not None else route
        created_route_record: typing.Optional[RouteRecord] = None
        if key is None or not key:
            key = '.'.join(tuple(chunks[1:] if chunks[0] == '' else chunks))
        _key, key = key, None
        _handler, handler = handler, None
        _chunks = []
        for chunk in chunks:
            _chunks.append(chunk)
            if chunk == '':
                continue
            normalized_chunk, dictionary_key, rule_name, _ = _parse_route_chunk(chunk)
            rule = rule_name
            for _rule in self.rules:
                if _rule.name == rule:
                    rule = _rule
                    break
            if '/'.join(_chunks) == '/'.join(chunks):
                key = _key
                handler = _handler

                exists = any(
                    nm['route'] == route
                    and nm['method'] == method
                    and nm['content_type'] == content_type
                    for nm in self._routes_by_key.get(key, [])
                )
                if len(self._routes_by_key.get(key, [])) == 0 or not exists:
                    route_record = {
                        "key": key,
                        "route": route,
                        "canonical_route": canonical_route,
                        "aliases": aliases or [],
                        'method': method,
                        'content_type': content_type,
                        'method_upper': (method or '*').upper() if method else '*',
                        'content_type_lower': (content_type or '').lower() if content_type else '',
                        'redirect': redirect,
                        'handler': handler,
                        'instance': self,
                    }
                    self.nodes_map.append(route_record)
                    self._routes_by_key[key].append(route_record)
                    self._routes_by_path[_route_path_key(route)].append(route_record)
                    created_route_record = route_record
            node = node.instance(normalized_chunk, full_route=full_route, key=key, dictionary_key=dictionary_key, rule=rule)
        if handler is None:
            raise Exception('The route handler was not attached')
        route_handler = typing.cast(typing.Any, handler)
        route_handler.node = node
        if created_route_record is not None and created_route_record not in node.route_records:
            node.route_records.append(created_route_record)
        route_handler.full_route = full_route
        route_handler.canonical_route = canonical_route
        route_handler.aliases = aliases or []

        if method == '*' and route_handler.__name__ in self.legal_http_method:
            route_handler.method = route_handler.__name__
        elif not hasattr(route_handler, 'method') or not route_handler.method:
            route_handler.method = method
        if not hasattr(route_handler, 'content_type') or not route_handler.content_type:
            route_handler.content_type = content_type
        if not hasattr(route_handler, 'redirect') or not route_handler.redirect:
            route_handler.redirect = redirect
        return route_handler

    def init(self, route, *args, key=None, module=None, method=None, content_type=None,
             redirect: typing.Optional[str] = None, **kwargs):
        """
        Декоратор функции обработки маршрута

        :param route: Маршрут
        :param key: Ключ маршрута
        :param module: Настройки модуля обработки
        :param method: Метод маршрута
        :param content_type: Тип контента маршрута
        :param redirect: Редирект, для маршрута
        :return:
        """

        def decorator(func):
            func = self._trigger_set_handler(func, *args, **kwargs)
            self.add(route, key=key, module=module, handler=func, method=method, content_type=content_type,
                     redirect=redirect)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper

        return decorator

    def controller(self, route, *args, model: typing.Optional[Schema] = None,
                   security: typing.Optional[SecurityDeclaration] = None, **kwargs):
        """
        Регистрация контроллера для обработки запросов классом

        :param model: Модель данных
        :param route: Маршрут
        :return:
        """

        def decorator(func):
            func.actions = []
            func.security = []
            func = self._trigger_set_controller(func, *args, **kwargs)
            for name in func.__dict__:
                method = func.__dict__[name]

                _security = []
                if security is not None:
                    for item in security:
                        if isinstance(item, BaseSecurity):
                            _security.append({item.securitySchema: []})
                        else:
                            _security.append({item: []})
                    func.security = _security

                if hasattr(method, "is_action"):
                    method.controller_class = func.__name__
                    method.controller = func
                    if len(func.security) > 0:
                        for item in func.security:
                            if item not in method.security:
                                method.security.append(item)
                    func.actions.append(name)
                    if not hasattr(method, 'model'):
                        method.model = model
                    _route = '/'.join(list(filter(None, route.split('/'))) + [method.route])
                    method = self._trigger_set_handler(method, *args, **kwargs)
                    self.add(_route, key=method.key, module=method.module, handler=method, method=method.method,
                             content_type=method.content_type, redirect=method.redirect)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper

        return decorator

    def action(self, *args, route=None, key=None, module=None, method=None, content_type=None,
               redirect: typing.Optional[str] = None, model: typing.Optional[Schema] = None,
               security: typing.Optional[SecurityDeclaration] = None, **kwargs):
        """
        Регистрация "действия" для контроллера.
        Внимание: Работает только совместно с регистрацией контроллера с помощью метода controller

        :param model: Модель данных
        :param route: Маршрут
        :param key: Ключ маршрута
        :param module: Настройки модуля обработки
        :param method: Метод маршрута
        :param content_type: Тип контента маршрута
        :param redirect: Редирект, для маршрута
        :param security: Необходимость и способ авторизации
        :return:
        """

        def decorator(func):
            kwargs['route'] = route or '/'
            kwargs['key'] = key
            kwargs['module'] = module
            kwargs['method'] = method
            kwargs['content_type'] = content_type
            kwargs['model'] = model
            kwargs['security'] = security
            kwargs['is_action'] = True
            func = self._trigger_set_handler(func, *args, **kwargs)

            func.is_action = True
            func.key = key
            func.module = module
            func.method = method
            if func.method == '*' and func.__name__ in self.legal_http_method:
                func.method = func.__name__
            func.content_type = content_type
            func.redirect = redirect
            func.route = route or '/'
            if model:
                func.model = model
            func._requires_auth = bool(getattr(func, "security", []))
            func._allowed_kwargs = frozenset(inspect.signature(func).parameters.keys())

            @wraps(func)
            def wrapper(*args, **kwargs):
                # validate(instance={"name": "Eggs", "price": 34.99}, schema=schema)
                requires_auth = func._requires_auth or bool(getattr(wrapper, "security", getattr(func, "security", [])))
                if "request" in kwargs and requires_auth and isinstance(kwargs["request"].user, GuestUser):
                    raise AccessDeniedException(reason="Access Denied")
                else:
                    unreliable = [key for key in kwargs.keys() if key not in func._allowed_kwargs]
                    if len(unreliable) > 0:
                        raise ApplicationException(status=500,
                                                   reason="The `%s` handler has no mandatory `%s` arguments" % (
                                                       func.__name__,
                                                       '`,`'.join(unreliable)
                                                   ),
                                                   body=traceback.format_exc())
                    return func(*args, **kwargs)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            setattr(wrapper, "security", getattr(func, "security", []))
            return wrapper

        return decorator

    def add_error_handler(self, code=None, handler=None):
        """
        Добавляет функцию обработки ошибки

        :param code: Код ошибки
        :param handler: функция обработки ошибки
        :return:
        """
        for c in self.error_handler_map:
            if code == c['code']:
                raise Exception('Error Handler must have unique `code` [%s]' % (code))
        if handler is None:
            raise Exception('Error Handler must have `handler`')
        self.error_handler_map.append({
            "code": code,
            "handler": handler,
        })
        if code is None:
            self._default_error_handler = handler
        else:
            self._error_handlers_by_code[code] = handler

    def map_error(self, exception, status=500, handler=None):
        if not inspect.isclass(exception) or not issubclass(exception, BaseException):
            raise TypeError("exception must be an Exception subclass")
        self._error_status_by_exception[exception] = status
        if handler is not None:
            self._error_handlers_by_exception[exception] = handler
        return handler

    def error_handler(self, code=None):
        """
        Декоратор функции ошибки

        :param code: Код ошибки, который эта функция будет обрабатывать
        :return:
        """

        def decorator(func):
            self.add_error_handler(code=code, handler=func)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper

        return decorator

    def _find_exception_error_mapping(self, error):
        for exception in type(error).mro():
            if exception in self._error_status_by_exception or exception in self._error_handlers_by_exception:
                return (
                    self._error_status_by_exception.get(exception),
                    self._error_handlers_by_exception.get(exception),
                )
        return None, None

    def get_current_route(self, request):
        """
        Получает узел роуттера из объекта запроса

        :param request: Объект запроса
        :return:
        """
        node, dictionary = self.match_with_params(request.path)
        if not isinstance(node, Node):
            return None, ()
        request_method = request.method.upper()
        request_content_type = request.content_type.lower()

        path_key = _route_path_key(getattr(node, "full_route", None) or "")
        key_candidates = self._routes_by_key.get(node.key, []) if node.key is not None else []
        candidates = getattr(node, "route_records", None) or self._routes_by_path.get(path_key) or key_candidates

        def condition(route):
            """condition here"""
            res = True
            if res and route['method'] and route['method'] != '*' and route['method_upper'] != request_method:
                res = False
            if res and route['content_type'] and route['content_type'] != '*/*' and \
                    route['content_type_lower'] != request_content_type:
                res = False
            return res

        filtered = [route for route in candidates if condition(route)]
        return filtered[0] if len(filtered) > 0 else None, dictionary

    def get_current_error_handler(self, error):
        """
        Возвращает функцию обработки ошибки

        :param error: код ошибки
        :return:
        """

        status, handler = self._find_exception_error_mapping(error) if isinstance(error, BaseException) else (None, None)
        if status is not None and not hasattr(error, "status"):
            setattr(error, "status", status)
        if handler:
            return {"code": status, "handler": handler}

        status = status or getattr(error, "status", None)
        handler = self._error_handlers_by_code.get(status)
        if handler:
            return {"code": status, "handler": handler}
        if self._default_error_handler:
            return {"code": None, "handler": self._default_error_handler}
        return None

    def print_tree(self):
        """
        Печатает дерево маршрутов

        :return:
        """
        logger = getattr(self, "logger", None) or logging.getLogger("muscles.router")
        route_map = self.nodes_map

        def tree(node, i):
            for r in node.childrens:
                i = i + 1
                meth = [_m['method'] or '*' for _m in route_map if r.key == _m['key']]
                logger.debug(
                    "%s /%s    [%s key:%s]",
                    '. ' * i,
                    r.route,
                    ','.join(meth).upper(),
                    r.key,
                )
                tree(r, i)
                i = i - 1

        tree(self.node, 0)


class Node(ABC):
    """
    Класс узла роутера
    """
    route: typing.Optional[str] = None
    rule: typing.Any = None
    name: typing.Optional[str] = None
    key: typing.Optional[str] = None
    method: typing.Optional[str] = None
    content_type: typing.Optional[str] = None
    full_route: typing.Optional[str]
    parent: typing.Optional["Node"]
    weight: int
    dictionary_key: typing.Optional[str]
    _childrens: list["Node"]
    _children_by_route: dict[typing.Optional[str], "Node"]
    route_records: list[RouteRecord]

    def __init__(self, chunk_route, key=None, full_route=None, dictionary_key=None, rule=None,
                 parent: typing.Optional["Node"] = None):
        """
        Конструктор класса роутера

        :param chunk_route: Адресс узла
        :param key: ключ узла
        :param dictionary_key: Словарь узла
        :param rule: Правило узла
        :param parent: Родитель узла
        """
        self.full_route = full_route
        chunk_route, _, _, has_param = _parse_route_chunk(chunk_route)
        self.key = key.lower() if key and key is not None else None
        self.route = chunk_route.lower() if chunk_route and chunk_route is not None else None
        self.rule = rule
        self.full_route = full_route.lower() if full_route and full_route is not None else None
        self.parent = parent
        self.weight = 100 if has_param else 0
        self.dictionary_key = dictionary_key.lower() if dictionary_key and dictionary_key is not None else None
        self._childrens = []
        self._children_by_route = {}
        self.route_records = []
        if self.parent is not None:
            self.parent._childrens.append(self)
            self.parent._childrens.sort(key=lambda node: node.weight)
            self.parent._children_by_route[self.route] = self

    def get_children_node(self, chunk_route):
        """
        Находит потомков узла
        :param chunk_route: Узел для поиска
        :return:
        """
        return self._children_by_route.get(chunk_route.lower())

    def instance(self, chunk_route, key=None, full_route=None, dictionary_key=None, rule=None) -> "Node":
        """
        Формирует узел

        :param full_route:
        :param chunk_route: Адресс узла
        :param key: ключ узла
        :param dictionary_key: Словарь узла
        :param rule: Правило узла
        :return: Node
        """
        chunk_route, _, _, _ = _parse_route_chunk(chunk_route)
        node = self.get_children_node(chunk_route)
        if node:
            if node.key is None:
                node.key = key
            return node
        else:
            return Node(chunk_route, key=key, full_route=full_route, dictionary_key=dictionary_key,
                        rule=rule, parent=self)

    def is_match(self, path):
        """
        Проверяет совпадает ли путь с правилом узла
        :param path: путь роутера
        :return:
        """
        return True if self.rule.is_match(path, self.route) else False

    def dictionary(self, chunk):
        """
        Словарь запроса

        :param chunk: часть пути узла
        :return:
        """
        return {self.dictionary_key: unquote(chunk)}

    @property
    def childrens(self):
        """
        Потомки узла
        :return:
        """
        return self._childrens

    def set_parent(self, parent, rule=None):
        """
        Устанавливает родителя узла
        :param parent: Родитель узла
        :param rule:
        :return:
        """
        self.parent = parent
