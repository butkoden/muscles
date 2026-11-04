from __future__ import annotations
import inspect
import typing
from dataclasses import dataclass
from functools import wraps
from threading import RLock


class DependencyError(LookupError):
    """Base error for keyed dependency resolution."""


class DependencyNotFoundError(DependencyError):
    """No candidate or fallback is registered for a dependency key."""


class DependencyProviderNotApplicable(DependencyError):
    """The selected provider cannot handle the current request context."""


class AmbiguousDependencyError(DependencyError):
    """Multiple candidates share the highest priority."""


@dataclass(frozen=True)
class KeyedDependencyRegistration:
    key: str
    provider: typing.Any
    priority: int | None
    is_default: bool
    args: tuple[typing.Any, ...] = ()
    kwargs: dict[str, typing.Any] | None = None

    @property
    def provider_name(self) -> str:
        provider_type = self.provider if inspect.isclass(self.provider) else self.provider.__class__
        module = getattr(provider_type, "__module__", None)
        name = getattr(provider_type, "__qualname__", provider_type.__name__)
        return f"{module}.{name}" if module else name


class DependencyRegistry:
    """Named dependencies with one fallback and priority-ordered providers."""

    def __init__(self):
        self._defaults: dict[str, KeyedDependencyRegistration] = {}
        self._providers: dict[str, list[KeyedDependencyRegistration]] = {}
        self._lock = RLock()

    def provide(self, key: str, provider: typing.Any, *args, **kwargs):
        key = self._validate_key(key)
        registration = KeyedDependencyRegistration(key, provider, None, True, args, dict(kwargs))
        with self._lock:
            current = self._defaults.get(key)
            if current is not None and current.provider is not provider:
                raise ValueError(f"Default provider for dependency `{key}` is already registered")
            self._defaults[key] = registration
        return provider

    def register(self, key: str, provider: typing.Any, *, priority: int = 0, args=(), kwargs=None):
        key = self._validate_key(key)
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise TypeError("Dependency priority must be an integer")
        registration = KeyedDependencyRegistration(
            key, provider, priority, False, tuple(args), dict(kwargs or {})
        )
        with self._lock:
            providers = self._providers.setdefault(key, [])
            for current in providers:
                if current.provider is provider:
                    if current.priority != priority:
                        raise ValueError(
                            f"Provider `{registration.provider_name}` for `{key}` was registered with different priorities"
                        )
                    return provider
            providers.append(registration)
        return provider

    def resolve(self, key: str):
        key = self._validate_key(key)
        with self._lock:
            providers = tuple(self._providers.get(key, ()))
            fallback = self._defaults.get(key)
        if providers:
            priority = max(provider.priority for provider in providers)
            winners = [provider for provider in providers if provider.priority == priority]
            if len(winners) != 1:
                names = ", ".join(sorted(provider.provider_name for provider in winners))
                raise AmbiguousDependencyError(
                    f"Dependency `{key}` has multiple providers at priority {priority}: {names}"
                )
            return self._build(winners[0])
        if fallback is None:
            raise DependencyNotFoundError(f"Dependency `{key}` is not registered")
        return self._build(fallback)

    def resolve_candidates(self, key: str) -> list[typing.Any]:
        key = self._validate_key(key)
        with self._lock:
            providers = tuple(self._providers.get(key, ()))
            fallback = self._defaults.get(key)
        priorities = [provider.priority for provider in providers]
        if len(priorities) != len(set(priorities)):
            raise AmbiguousDependencyError(f"Dependency `{key}` has providers with equal priorities")
        candidates = sorted(providers, key=lambda provider: provider.priority, reverse=True)
        if fallback is not None:
            candidates.append(fallback)
        if not candidates:
            raise DependencyNotFoundError(f"Dependency `{key}` is not registered")
        return [self._build(candidate) for candidate in candidates]

    def list(self, key: str | None = None) -> list[dict[str, typing.Any]]:
        with self._lock:
            keys = [self._validate_key(key)] if key is not None else sorted(
                set(self._defaults) | set(self._providers)
            )
            defaults = dict(self._defaults)
            providers_by_key = {item_key: tuple(value) for item_key, value in self._providers.items()}
            registrations = [
                registration
                for item_key in keys
                for registration in (
                    ([defaults[item_key]] if item_key in defaults else [])
                    + list(providers_by_key.get(item_key, ()))
                )
            ]
        result = []
        for item_key in keys:
            candidates = [item for item in registrations if item.key == item_key and not item.is_default]
            winner = None
            if candidates:
                highest = max(item.priority for item in candidates)
                highest_candidates = [item for item in candidates if item.priority == highest]
                if len(highest_candidates) == 1:
                    winner = highest_candidates[0]
            elif item_key in defaults:
                winner = defaults[item_key]
            result.extend(
                {
                    "key": item.key,
                    "provider": item.provider_name,
                    "priority": item.priority,
                    "default": item.is_default,
                    "selected": item is winner,
                }
                for item in registrations
                if item.key == item_key
            )
        return result

    @staticmethod
    def _validate_key(key: str) -> str:
        if not isinstance(key, str) or not key.strip() or key != key.strip():
            raise ValueError("Dependency key must be a non-empty string without surrounding whitespace")
        return key

    @staticmethod
    def _build(registration: KeyedDependencyRegistration):
        provider = registration.provider
        args = registration.args
        kwargs = registration.kwargs or {}
        if inspect.isclass(provider) or callable(provider):
            return provider(*args, **kwargs)
        if args or kwargs:
            raise TypeError("Arguments can only be supplied when a dependency provider is callable")
        return provider


class DependencyStorage:
    _storages = {}
    _history = {}
    _instances: dict[type, typing.Any] = {}

    def __call__(self, *args, **kwargs):
        """
        Данная реализация не учитывает возможное изменение передаваемых
        аргументов в `__init__`

        :param args:
        :param kwargs:
        :return:
        """
        cls = type(self)
        if cls not in cls._instances:
            cls._instances[cls] = self
        return cls._instances[cls]

    def add(self, dependency, inject, *args, **kwargs):
        """ Добавляет в хранилище зависимостей информацию о новой зависимости.
            Если зависимость уже присутствует в хранилище и аргументов не передано тогда происходит замена
            зависимости на новую, но с тем же интерфейсом.
        """
        if dependency.__name__ not in self._storages:
            self._storages[dependency.__name__] = (inject, args, kwargs)
            self._history[dependency.__name__] = []
            self._history[dependency.__name__].append(inject)
        elif len(args) <= 0:
            self._storages[dependency.__name__] = self.construct(dependency, inject)
            self._history[dependency.__name__].append(inject)
        else:
            raise Exception('Attempt to update the dependency %s with replacement of input data' % dependency.__name__)

    def rollback(self, dependency):
        if dependency.__name__ not in self._storages:
            return False
        self._history[dependency.__name__].pop()
        inject = self._history[dependency.__name__][-1]
        self._storages[dependency.__name__] = self.construct(dependency, inject)
        return True

    def construct(self, dependency, inject):
        if dependency.__name__ not in self._storages:
            return False
        return (
            inject,
            self._storages[dependency.__name__][1],
            self._storages[dependency.__name__][2]
        )

    def get(self, dependency):
        """ Возвращает из хранилища зависимостей информацию о выбранной зависимости """
        if dependency.__name__ not in self._storages:
            raise Exception('Dependency %s not found' % dependency.__name__)

        try:
            return self._storages[dependency.__name__][0](
                *self._storages[dependency.__name__][1],
                **self._storages[dependency.__name__][2]
            )
        except Exception as e:
            print("Dependency %s not founded" % dependency.__name__)
            raise e


def inject(*drugs, progressive=True):
    """ Декоратор указывающий функции или методу о том какие зависимости нужно удовлетворить.
    :param progressive - указывает на способ обработки зависимостей

    Пример 1: progressive=False

        ```
        class TestInterface:
            pass

        class TestDependency(TestInterface):
            def test(self):
                return "Active 1"

        Dependency(TestInterface, TestDependency)

        @inject(progressive=False)
        def main(test: TestInterface = Dependency(TestInterface)):
            print('-->', test.test())
            assert test.test() == 'Active 1'
        ```

    Пример 2: progressive=True

        ```
        class TestInterface:
            pass

        class TestDependency(TestInterface):
            def test(self):
                return "Active 1"

        Dependency(TestInterface, TestDependency)

        @inject(TestInterface, progressive=True)
        def main(test: TestInterface):
            print('-->', test.test())
            assert test.test() == 'Active 1'
        ```
    """
    def decorator(func):
        ds = DependencyStorage()
        signature = inspect.signature(func)
        params = signature.parameters

        @wraps(func)
        def wrapper(*args, **kwargs):
            if progressive is True:
                for name, param in params.items():
                    if param.annotation is not inspect._empty \
                            and param.annotation in drugs \
                            and (param.default is inspect._empty or param.default is None) \
                            and name not in kwargs:
                        kwargs[name] = ds.get(param.annotation)
            else:
                for name, param in params.items():
                    if isinstance(param.default, Dependency):
                        if name not in kwargs:
                            kwargs[name] = ds.get(param.default.dependency)
            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


class Dependency:
    """
    Контекст определяет интерфейс, представляющий интерес для клиентов.
    """

    _storages = {}
    _keyed_registry = DependencyRegistry()

    @classmethod
    def provide(cls, key: str, provider: typing.Any, *args, **kwargs):
        """Register the fallback provider used when a key has no candidates."""
        return cls._keyed_registry.provide(key, provider, *args, **kwargs)

    @classmethod
    def get(cls, key: str):
        """Resolve the highest-priority provider registered for a string key."""
        return cls._keyed_registry.resolve(key)

    @classmethod
    def get_candidates(cls, key: str) -> list[typing.Any]:
        """Return providers in priority order, followed by the fallback if present."""
        return cls._keyed_registry.resolve_candidates(key)

    @classmethod
    def list(cls, key: str | None = None) -> list[dict[str, typing.Any]]:
        """List keyed registrations and indicate which provider would be selected."""
        return cls._keyed_registry.list(key)

    def __init__(self, dependency, *args, **kwargs) -> None:
        """
        Обычно Контекст принимает стратегию через конструктор, а также
        предоставляет сеттер для её изменения во время выполнения.
        """
        self._owner = None
        if len(args) > 0:
            ds = DependencyStorage()
            ds.add(dependency, args[0], *args[1:], **kwargs)
        self._dependency = dependency

    def __set_name__(self, owner, name):
        self._name = name
        self.set_container(owner)

    def set_container(self, owner):
        """
        Устанавливаем объект в контейнер контекста

        :param owner: объект контекста
        :return:
        """
        self._owner = owner

    @property
    def dependency(self):
        """
        Возвращает зависимость, которую нужно удовлетворить.
        """
        return self._dependency

    @staticmethod
    def init(interface, *args, **kwargs):
        """ Устанавливает зависимость для класса или функции

        Пример:
            ```
            class TestInterface:
                pass

            @Dependency.init(TestInterface, "val1", kwarg2=1)
            class TestDependency(TestInterface):
                def test(self, arg1, kwarg2=None):
                    return arg1 + ' ' + kwarg2  # return > "val1 1"

            Dependency(TestInterface, TestDependency)
            @inject(TestInterface)
            def main(test: TestInterface):
                print('-->', test.test())
                assert test.test() == 'Active 1'
            ```

        """

        if isinstance(interface, str):
            priority = kwargs.pop("priority", 0)

            def keyed_decorator(provider):
                Dependency._keyed_registry.register(
                    interface,
                    provider,
                    priority=priority,
                    args=args,
                    kwargs=kwargs,
                )
                return provider

            return keyed_decorator

        def decorator(func):
            ds = DependencyStorage()
            ds.add(interface, func, *args, **kwargs)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper

        return decorator

    @staticmethod
    def change(interface):
        """ Заменяет зависимость для класса или функции.

        Пример:
            ```
            class TestInterface:
                pass

            @Dependency.init(TestInterface, "val1", kwarg2=1)
            class TestDependency(TestInterface):
                def test(self, arg1, kwarg2=None):
                    return arg1 + ' ' + kwarg2  # return > "val1 1"

            @Dependency.change(TestInterface, "val1", kwarg2=1)
            class Test2Dependency(TestInterface):
                def test(self, arg1, kwarg2=None):
                    return arg1 + ' ' + kwarg2  # return > "val1 1"

            Dependency(TestInterface, TestDependency)
            @inject(TestInterface)
            def main(test: TestInterface):
                print('-->', test.test())
                assert test.test() == 'Active 1'
            ```

        """

        def decorator(func):
            ds = DependencyStorage()
            ds.add(interface, func)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper

        return decorator

    @staticmethod
    def resolve(interface):
        ds = DependencyStorage()
        return ds.get(interface)

    def __get__(self, instance, owner):
        """ Возвращаем зависимость при обращении к объекту """
        ds = DependencyStorage()
        return ds.get(self._dependency)

    def __set__(self, key, inject):
        """ Если напрямую указываем объект в переменную DI то заменяем им зависимость"""
        ds = DependencyStorage()
        return ds.add(self._dependency, inject)

    def __call__(self, *args, **kwargs):
        """ Разрешаем при вызове объекта Dependency подставлять вызываемый объект через зависимость"""
        ds = DependencyStorage()
        return ds.get(self._dependency)

    def __str__(self):
        ds = DependencyStorage()
        dep = ds.get(self._dependency)
        return "%s object at %s is dependency %s" % (self.__class__, id(self), dep.__class__)

    def __enter__(self):
        """ Метод для входа в контекст
        Пример:
        ```
        with Dependency(TestAppInterface, TestApp1) as di:
            assert di.test() == 'Active 1'
        ```
        """
        ds = DependencyStorage()
        dep = ds.get(self._dependency)
        return dep

    def __exit__(self, exc_type, exc_value, traceback):
        """ Вызывается при выходе из контекста with """
        ds = DependencyStorage()
        ds.rollback(self._dependency)
