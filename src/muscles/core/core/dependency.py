from __future__ import annotations
import inspect
from functools import wraps


class DependencyStorage:
    _storages = {}
    _history = {}
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Данная реализация не учитывает возможное изменение передаваемых
        аргументов в `__init__`

        :param args:
        :param kwargs:
        :return:
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
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
