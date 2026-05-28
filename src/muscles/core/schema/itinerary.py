import inspect
import re
import os
import traceback
from collections import defaultdict
from functools import wraps
from abc import ABC
from urllib.parse import unquote

from ..exceptions import ApplicationException, AccessDeniedException
from .schema import Schema
from .security import BaseSecurity
from .user import GuestUser


HTTP_METHOD_GET = 'get'
HTTP_METHOD_POST = 'post'
HTTP_METHOD_PUT = 'put'
HTTP_METHOD_DELETE = 'delete'
HTTP_METHOD_HEAR = 'head'
HTTP_METHOD_PATCH = 'patch'
HTTP_METHOD_OPTION = 'options'
HTTP_METHOD_TRACE = 'trace'
HTTP_METHOD_CONNECT = 'connect'

class Itinerary:
    """
    Базовый класс для работы с роутами
    """

    legal_http_method = [HTTP_METHOD_GET, HTTP_METHOD_POST, HTTP_METHOD_PUT, HTTP_METHOD_DELETE, HTTP_METHOD_HEAR, 
                         HTTP_METHOD_PATCH, HTTP_METHOD_OPTION, HTTP_METHOD_TRACE, HTTP_METHOD_CONNECT]
    

    # nodes_map = []
    # static_map = []
    error_handler_map = []
    rules = []
    node = None
    _instances = {}

    set_response = {}

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
            instance = super(Itinerary, cls).__new__(cls)
            instance.node = Node('')
            instance.prefix = prefix
            instance.nodes_map = []
            instance.static_map = []
            instance._routes_by_key = defaultdict(list)
            instance._error_handlers_by_code = {}
            instance._default_error_handler = None
            instance._match_cache = {}
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

    def to_url(self, route_key, params):
        """
        Формирует из ключа маршрута и параметров ссылку

        :param route_key: Ключ маршрута
        :param params: Параметры
        :return:
        """
        l = []

        def repl(m):
            name = m.group(3) if m.group(3) else 'var'
            for rule in self.rules:
                if rule.name == name:
                    return rule.compile(params.get(m.group(2), ''))

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
        chunks = url.split('/')
        if len(chunks) > 0 and chunks[0] == '':
            chunks = chunks[1:]
        for route in self._match(self.node, chunks):
            if route.key and route.key in self._routes_by_key:
                self._match_cache[url] = route
                return route
        self._match_cache[url] = False
        return None

    def _match(self, route, chunks, paths=None, n=0):
        """
        Поиск подходящих узлов

        :param route:
        :param chunks:
        :param paths:
        :param n:
        :return:
        """
        if paths is None:
            paths = []
        if len(chunks) == 0:
            return
        for node in route.childrens:
            if node.is_match(chunks[:1][0]):
                if len(chunks[1:]) == 0:
                    yield node
                else:
                    yield from self._match(node, chunks[1:], [node] + paths, n + 1)

    def match_with_params(self, url):
        """
        Возвращает подходящий маршрут с параметрами

        :param url: УРЛ
        :return:
        """
        chunks = url.split('/')
        node = self.match(url)
        if node is None:
            return None, {}
        _node = node
        dictionary = {}
        for chunk in chunks[::-1]:
            if _node.dictionary_key:
                dictionary.update(_node.dictionary(chunk))
            _node = _node.parent
        return node, dictionary

    def add_static(self, directory: str, prefix: str = None, handler=None, full_path: bool = False):
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

    def static(self, directory: str, prefix: str = None, full_path: bool = False):
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
        handler.is_action = kwargs.get('is_action', False)
        handler.key = kwargs.get('key')
        handler.module = kwargs.get('module')
        handler.method = kwargs.get('method')
        handler.content_type = kwargs.get('content_type')
        handler.redirect = kwargs.get('redirect')
        handler.route = kwargs.get('route', '/')
        handler.model = kwargs.get('model')
        return handler

    def _trigger_set_controller(self, handler, *args, **kwargs):
        return handler

    def add(self, route, key=None, handler=None, method=None, content_type=None,
            redirect: str = None, module=None):
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
        if key is None or not key:
            key = '.'.join(tuple(chunks[1:] if chunks[0] == '' else chunks))
        _key, key = key, None
        _handler, handler = handler, None
        _chunks = []
        for chunk in chunks:
            _chunks.append(chunk)
            if chunk == '':
                continue
            m = re.search(r"\{([^\}]+)\}", chunk)
            if m:
                m = m.group(1).split(':')
                dictionary_key = m[0]
                rule = m[1] if len(m) > 1 else 'var'
            else:
                dictionary_key = False
                rule = 'default'
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
                        'method': method,
                        'content_type': content_type,
                        'redirect': redirect,
                        'handler': handler,
                        'instance': self,
                    }
                    self.nodes_map.append(route_record)
                    self._routes_by_key[key].append(route_record)
            node = node.instance(chunk, full_route=full_route, key=key, dictionary_key=dictionary_key, rule=rule)
        handler.node = node
        handler.full_route = full_route

        if method == '*' and handler is not None and handler.__name__ in self.legal_http_method:
            handler.method = handler.__name__
        elif not hasattr(handler, 'method') or not handler.method:
            handler.method = method
        if not hasattr(handler, 'content_type') or not handler.content_type:
            handler.content_type = content_type
        if not hasattr(handler, 'redirect') or not handler.redirect:
            handler.redirect = redirect
        return handler

    def init(self, route, *args, key=None, module=None, method=None, content_type=None,
             redirect: str = None, **kwargs):
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

    def controller(self, route, *args, model: Schema = None, security: list[BaseSecurity, str] = None, **kwargs):
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
               redirect: str = None, model: Schema = None, security: list[BaseSecurity, str] = None, **kwargs):
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

            @wraps(func)
            def wrapper(*args, **kwargs):
                # validate(instance={"name": "Eggs", "price": 34.99}, schema=schema)
                if "request" in kwargs and len(func.security) > 0 and isinstance(kwargs["request"].user, GuestUser):
                    raise AccessDeniedException(reason="Access Denied")
                else:
                    signature = inspect.signature(func)
                    params = signature.parameters
                    unreliable = list(set(kwargs.keys()) - set(params.keys()))
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

    def get_current_route(self, request):
        """
        Получает узел роуттера из объекта запроса

        :param request: Объект запроса
        :return:
        """
        node, dictionary = self.match_with_params(request.path)
        if node is None:
            return None, ()

        def condition(route):
            """condition here"""
            res = True
            if res and route['key'] and route['key'] != node.key:
                res = False
            if res and route['method'] and route['method'] != '*' and route['method'].upper() != request.method.upper():
                res = False
            if res and route['content_type'] and route['content_type'] != '*/*' and \
                    route['content_type'].lower() != request.content_type.lower():
                res = False
            return res

        filtered = [route for route in self._routes_by_key.get(node.key, []) if condition(route)]
        return filtered[0] if len(filtered) > 0 else None, dictionary

    def get_current_error_handler(self, error):
        """
        Возвращает функцию обработки ошибки

        :param error: код ошибки
        :return:
        """

        handler = self._error_handlers_by_code.get(error.status)
        if handler:
            return {"code": error.status, "handler": handler}
        if self._default_error_handler:
            return {"code": None, "handler": self._default_error_handler}
        return None

    def print_tree(self):
        """
        Печатает дерево маршрутов

        :return:
        """
        map = self.nodes_map

        def tree(node, i):
            for r in node.childrens:
                i = i + 1
                meth = [_m['method'] or '*' for _m in map if r.key == _m['key']]
                print('. ' * i, '/%s' % r.route, ' ' * 3, '[%s key:%s]' % (','.join(meth).upper(), r.key))
                tree(r, i)
                i = i - 1

        tree(self.node, 0)


class Node(ABC):
    """
    Класс узла роутера
    """
    route = None
    rule = None
    name = None
    dictionary = None
    key = None
    method = None
    content_type = None

    def __init__(self, chunk_route, key=None, full_route=None, dictionary_key=None, rule=None, parent=None):
        """
        Конструктор класса роутера

        :param chunk_route: Адресс узла
        :param key: ключ узла
        :param dictionary_key: Словарь узла
        :param rule: Правило узла
        :param parent: Родитель узла
        """
        self.full_route = full_route
        m = re.search(r"\{([^\}]+)\}", chunk_route)
        if m:
            m = m.group(1).split(':')
            chunk_route = '{%s:%s}' % (m[0], m[1] if len(m) > 1 else 'var')
        self.key = key.lower() if key and key is not None else None
        self.route = chunk_route.lower() if chunk_route and chunk_route is not None else None
        self.rule = rule
        self.full_route = full_route.lower() if full_route and full_route is not None else None
        self.parent = parent
        self.weight = 0 if not m else 100
        self.dictionary_key = dictionary_key.lower() if dictionary_key and dictionary_key is not None else None
        self._childrens = []
        self._children_by_route = {}
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

    def instance(self, chunk_route, key=None, full_route=None, dictionary_key=None, rule=None):
        """
        Формирует узел

        :param full_route:
        :param chunk_route: Адресс узла
        :param key: ключ узла
        :param dictionary_key: Словарь узла
        :param rule: Правило узла
        :return: Node
        """
        m = re.search(r"\{([^\}]+)\}", chunk_route)
        if m:
            m = m.group(1).split(':')
            chunk_route = '{%s:%s}' % (m[0], m[1] if len(m) > 1 else 'var')
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
