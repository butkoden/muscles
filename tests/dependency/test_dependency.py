from abc import abstractmethod
from muscles.core.core import Dependency
from muscles.core.core import inject
from muscles.core.core import ApplicationMeta


class TestInterface:
    @abstractmethod
    def test(self):
        return "Passive"


class Test1Dependency(TestInterface):
    def test(self):
        return "Active 1"


class Test2Dependency(TestInterface):
    def test(self):
        return "Active 2"


Dependency(TestInterface, Test1Dependency)


def test_dependency():
    """
    Базовая проверка на работоспособность зависимостей DI
    :return:
    """

    @inject(TestInterface)
    def main1(test: TestInterface):
        assert test.test() == 'Active 1'

    main1()

    Dependency(TestInterface, Test2Dependency)

    @inject(TestInterface)
    def main2(test: TestInterface):
        assert test.test() == 'Active 2'

    main2()


def test_dependency_non_progressive():
    """
    Проверяем в режиме удовлетворения зависимостей progressive=True и progressive=False
    :return:
    """

    Dependency(TestInterface, Test1Dependency)

    @inject(progressive=False)
    def main1(test: TestInterface = Dependency(TestInterface)):
        assert test.test() == 'Active 1'

    main1()

    Dependency(TestInterface, Test2Dependency)

    @inject(progressive=False)
    def main2(test: TestInterface = Dependency(TestInterface)):
        assert test.test() == 'Active 2'

    main2()


def test_dependency_nextgen():
    """
    Проверяем DI на инициализацию через декоратор
    :return:
    """

    class Test4Interface:

        def __init__(self, arg1, kwarg=None):
            pass

        @abstractmethod
        def test(self):
            return None

    @Dependency.init(Test4Interface, "val1", kwarg="one")
    class Test41Dependency(Test4Interface):

        def __init__(self, arg1, kwarg=None):
            super().__init__(arg1, kwarg=kwarg)
            self.arg1 = arg1
            self.kwarg = kwarg

        def test(self):
            return "Active 1" + self.arg1 + self.kwarg

    class Test42Dependency(Test4Interface):

        def __init__(self, arg1, kwarg=None):
            super().__init__(arg1, kwarg=kwarg)
            self.arg1 = arg1
            self.kwarg = kwarg

        def test(self):
            return "Active 2" + self.arg1 + self.kwarg

    @inject(Test4Interface)
    def main1(test: Test4Interface):
        assert test.test() == 'Active 1val1one'

    main1()

    Dependency(Test4Interface, Test42Dependency)

    @inject(Test4Interface)
    def main2(test: Test4Interface):
        assert test.test() == 'Active 2val1one'

    main2()


def test_dependency_nextgen2():
    """
    Проверяем DI на работу через декораторы
    :return:
    """

    class Test5Interface:

        def __init__(self, arg1, kwarg=None):
            pass

        @abstractmethod
        def test(self):
            return None

    @Dependency.init(Test5Interface, "val1", kwarg="one")
    class Test51Dependency(Test5Interface):

        def __init__(self, arg1, kwarg=None):
            super().__init__(arg1, kwarg=kwarg)
            self.arg1 = arg1
            self.kwarg = kwarg

        def test(self):
            return "Active 31" + self.arg1 + self.kwarg

    @inject(Test5Interface)
    def main1(test: Test5Interface):
        assert test.test() == 'Active 31val1one'

    main1()

    @Dependency.change(Test5Interface)
    class Test52Dependency(Test5Interface):

        def __init__(self, arg1, kwarg=None):
            super().__init__(arg1, kwarg=kwarg)
            self.arg1 = arg1
            self.kwarg = kwarg

        def test(self):
            return "Active 32" + self.arg1 + self.kwarg

    @inject(Test5Interface)
    def main2(test: Test5Interface):
        assert test.test() == 'Active 32val1one'

    main2()


def test_dependency_nextgen3():
    """
    Проверяем DI на работу с контекстом
    :return:
    """

    class Test6Interface:

        def __init__(self, arg1, kwarg=None):
            pass

        @abstractmethod
        def test(self):
            return None

    @Dependency.init(Test6Interface, "val1", kwarg="one")
    class Test61Dependency(Test6Interface):

        def __init__(self, arg1, kwarg=None):
            super().__init__(arg1, kwarg=kwarg)
            self.arg1 = arg1
            self.kwarg = kwarg

        def test(self):
            return "Active 31" + self.arg1 + self.kwarg

    class Test62Dependency(Test6Interface):

        def __init__(self, arg1, kwarg=None):
            super().__init__(arg1, kwarg=kwarg)
            self.arg1 = arg1
            self.kwarg = kwarg

        def test(self):
            return "Active 32" + self.arg1 + self.kwarg

    @inject(Test6Interface)
    def main1(test: Test6Interface):
        assert test.test() == 'Active 31val1one'

    main1()

    with Dependency(Test6Interface, Test62Dependency) as di:
        assert di.test() == 'Active 32val1one'

        @inject(Test6Interface)
        def main2(test: Test6Interface):
            assert test.test() == 'Active 32val1one'

        main2()


    @inject(Test6Interface)
    def main3(test: Test6Interface):
        assert test.test() == 'Active 31val1one'

    main3()


def test_dependency_with_app():
    """
    Проверяем DI совместно с ApplicationMeta
    :return:
    """
    class TestAppInterface:
        @abstractmethod
        def test(self):
            return "Active 0"

    class TestApp1:
        def test(self):
            return "Active 1"

    class TestApp2:
        def test(self):
            return "Active 2"

    class TestApp3:
        def test(self):
            return "Active 3"

    class App(metaclass=ApplicationMeta):
        di = Dependency(TestAppInterface, TestApp1)

    m = App()
    assert m.di.test() == 'Active 1'

    m.di = TestApp2
    assert m.di.test() == 'Active 2'

    Dependency(TestAppInterface, TestApp3)
    assert m.di.test() == 'Active 3'

    with Dependency(TestAppInterface, TestApp1) as di:
        assert di.test() == 'Active 1'
