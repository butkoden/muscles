# Пример работы с зависимостями Dependency (патерн Dependency Injection / DI)

Muscles содержит внутри себя возможность управления зависимостями через DI.

Благодаря этому механизму вы можете подключать различные способы работы с базами данных, добавлять модели, прокидывать 
объекты из одного пакета в другой и многое другое. Ниже рассмотрены основные способы взаимодействия с DI.


## Определение и переопределение зависимости

Зависимость определяется через объект ``Dependency``

Пример указания зависимости ``Dependency(TestInterface, Test1Dependency, arg1, kwarg1=1)``, где 
`TestInterface` - Интерфейс, который объеденяет наши сущности и является их общим  идентификатором.,
`Test1Dependency` - Объект, который реализует [TestInterface] и является законченной сущностью, которую мы получим после 
удовлетворения зависимости.
`arg1 и kwarg1=1` аргументы, который будут переданы в конструктор объекта __init__ при его создании, каждый раз, когда 
мы будем запрашивать удовлетворение зависимости.

Пример переопределения зависимости ``Dependency(TestInterface, Test2Dependency)``, где 
`TestInterface` - Интерфейс, который объеденяет наши сущности и является их общим  идентификатором.,
`Test2Dependency` - Объект, который реализует [TestInterface] и является законченной сущностью, которую мы получим после 
удовлетворения зависимости.

Как видите практически идентично установке зависимости, за исключением того что мы не передаем аргументы. 
Наш DI уже знает начальные условия и при запросе на удовлетворение подставить их из примера установки зависимости.


### Пример 1: Определение и переопределение зависимости
```python
from abc import abstractmethod
from muscles import Dependency
from muscles import inject

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

@inject(TestInterface)
def main(test: TestInterface):
    assert test.test() == 'Active 1'

main()

Dependency(TestInterface, Test2Dependency)

@inject(TestInterface)
def main(test: TestInterface):
    assert test.test() == 'Active 2'

main()

```


## Удовлетворение зависимости

После того как мы установили зависимость, мы можем запросить ее удовлетворение в функции или методе с помощью декоратора
``inject``. Декоратор содержит один опциональный параметр `progressive`, который указывает на способ обработки 
зависимостей.

При ``progressive=True`` необходимо в декторатор `inject` передать интерфейс вызываемой зависимости, так же этот же 
интерфейс должен быть указан как TypeHint к аргументу функции.

При ``progressive=False`` в дектораторе `inject` ничего указывать не нужно, но в функции необходимо присвоить 
дефолтное значение к аргументу как `Dependency(TestInterface)`.

Оба варианта использования могут пригодиться в тех или иных случаях. 
По умолчанию `progressive=True`


### Пример 1: progressive=False
```python
from muscles import Dependency
from muscles import inject

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


### Пример 2: progressive=True
```python
from muscles import Dependency
from muscles import inject

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


### Пример 3: Разрешение зависимости во время выполнения
```python
from muscles import Dependency

class TestInterface:
    pass

class TestDependency(TestInterface):
    def test(self):
        return "Active 1"

Dependency(TestInterface, TestDependency)

def main():
    print('-->', Dependency.resolve(TestInterface))
    assert Dependency.resolve(TestInterface) == 'Active 1'

```




## Определение и переопределение зависимости через декораторы

Существует и другой способ установки и переустановки зависимости через декораторы 
`@Dependency.init` и `@Dependency.change` соответственно. Ниже просто рассмотрим примеры работы с ними. 
Вся схема полностью повторяет обычную работу с зависимости.


### Пример 1: progressive=False
```python
from muscles import Dependency
from muscles import inject
from abc import abstractmethod

class TestInterface:

    def __init__(self, arg1, kwarg=None):
        pass

    @abstractmethod
    def test(self):
        return None

# Определяем зависимость
@Dependency.init(TestInterface, "val1", kwarg="one")
class TestDependency(TestInterface):

    def __init__(self, arg1, kwarg=None):
        super().__init__(arg1, kwarg=kwarg)
        self.arg1 = arg1
        self.kwarg = kwarg

    def test(self):
        return "Active 1" + self.arg1 + self.kwarg

@inject(TestInterface)
def main1(test: TestInterface):
    assert test.test() == 'Active 1val1one'

main1()

# переопределяем зависимость
@Dependency.change(TestInterface)
class Test2Dependency(TestInterface):

    def __init__(self, arg1, kwarg=None):
        super().__init__(arg1, kwarg=kwarg)
        self.arg1 = arg1
        self.kwarg = kwarg

    def test(self):
        return "Active 2" + self.arg1 + self.kwarg

@inject(TestInterface)
def main2(test: TestInterface):
    assert test.test() == 'Active 2val1one'

main2()

```


## Работа с контекстом

Как и в других случаях работа с контекстом происходит через оператор `with`. 

Рассмотрим пример `with Dependency(TestInterface, TestDependency) as di`, где 
`TestInterface` - интерфейс зависимости
`TestDependency` - объект, которым мы хотим ее удовлетворить
`di` - наш возвращенный объект, удовлетворяющий нашу зависимость.

На примере ниже показано, что внутри оператора `with` любая зависимость будет подчиняться выше упомянутой, однако 
сразу после выхода из контекста или после оператора `with` зависимость будет возращена назад. Если до with была 
`TestDefaultDependency`, то именно она и будет возращена. Таким образом вы можете в нужных участках локально переключать 
зависимость на подходящую, сохраняя в других местах дефолтную.

### Пример 1
```python
from muscles import Dependency
from muscles import inject
from abc import abstractmethod

class TestInterface:

    def __init__(self, arg1, kwarg=None):
        pass

    @abstractmethod
    def test(self):
        return None

# Определяем зависимость
@Dependency.init(TestInterface, "val1", kwarg="one")
class TestDependency(TestInterface):

    def __init__(self, arg1, kwarg=None):
        super().__init__(arg1, kwarg=kwarg)
        self.arg1 = arg1
        self.kwarg = kwarg

    def test(self):
        return "Active 1" + self.arg1 + self.kwarg
    
with Dependency(TestInterface, TestDependency) as di:
    assert di.test() == 'Active 1val1one'

    @inject(TestInterface)
    def main2(test: TestInterface):
        assert test.test() == 'Active 1val1one'
```


## Совместная работа с приложением `ApplicationMeta`

Часто необходимо определить зависимость для свойства объекта, и хоть это не обязательно, но в нашем примере мы 
оперделяем зависимость для объекта созданного по принципам ApplicationMeta. Это наш родительский объект приложения.

В примере ниже мы:

`di = Dependency(TestAppInterface, TestApp1)` - определяем нашу зависимость

`m.di.test()` - таким способом можем обратиться к ее методам

`m.di = TestApp2` - один из способов переопределения зависимости, это назначить ее свойству напрямую

`Dependency(TestAppInterface, TestApp3)` - так же ее можно переопределить из другого места программы, и при 
этом это изменит и `m.di.test()`

`with Dependency(TestAppInterface, TestApp1) as di:` - поменять ее в контексте

Важно обратить внимание, что декоратор `inject` работает с такими зависимостями прежним способом.


### Пример 1
```python
from muscles import Dependency
from abc import abstractmethod
from muscles import ApplicationMeta

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
```
