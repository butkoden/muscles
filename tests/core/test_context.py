from .app.instance import App
from .app.instance import Strategy
from muscles.core.core import BaseStrategy


def start_response(status, headers):
    pass



class Strategy1(BaseStrategy):
    def execute(self, *args, **kwargs):
        return "Strategy Apply 1"


class StrategyBefore(BaseStrategy):
    def execute(self, *args, **kwargs):
        return "Strategy Apply" + kwargs['before']


class StrategyConext(BaseStrategy):
    def execute(self, *args, **kwargs):
        return "Strategy Apply" + kwargs['context']


class Strategy2(BaseStrategy):
    def execute(self, *args, **kwargs):
        return "Strategy Apply 2"


class StrategyAfter(BaseStrategy):
    def execute(self, *args, **kwargs):
        return "Strategy Apply" + kwargs['after']


class StrategyAllTrigger(BaseStrategy):
    def execute(self, *args, **kwargs):
        return "Strategy Apply" + kwargs['before'] + kwargs['context'] + kwargs['after']


def test_context0():
    """
    Проверяем работоспособность схемы
    :return:
    """
    instance = App()
    instance.context.strategy = Strategy
    result = instance()
    assert result == 'Strategy Apply'


def test_context2_with_before():
    """
    Проверяем работоспособность схемы
    :return:
    """
    instance = App()
    instance.context.strategy = Strategy1
    result = instance()
    assert result == 'Strategy Apply 1'

    instance.context.strategy = StrategyBefore
    result = instance()
    assert result == 'Strategy ApplyAdd Before String'


def test_context3_with_context():
    """
    Проверяем работоспособность схемы
    :return:
    """
    instance = App()
    instance.context.strategy = StrategyBefore
    result = instance()
    assert result == 'Strategy ApplyAdd Before String'

    instance = App()
    instance.context.strategy = StrategyConext
    result = instance()
    assert result == 'Strategy ApplyAdd Context String'

    instance = App()
    instance.context.strategy = StrategyAfter
    result = instance()
    assert result == 'Strategy ApplyAdd After String'

    instance = App()
    instance.context.strategy = StrategyAllTrigger
    result = instance()
    assert result == 'Strategy ApplyAdd Before StringAdd Context StringAdd After String'
