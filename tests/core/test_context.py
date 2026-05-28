from .app.instance import Muscular
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
    muscular = Muscular()
    muscular.context.strategy = Strategy
    app = muscular()
    assert app == 'Strategy Apply'


def test_context2_with_before():
    """
    Проверяем работоспособность схемы
    :return:
    """
    muscular = Muscular()
    muscular.context.strategy = Strategy1
    app = muscular()
    assert app == 'Strategy Apply 1'

    muscular.context.strategy = StrategyBefore
    app = muscular()
    assert app == 'Strategy ApplyAdd Before String'


def test_context3_with_context():
    """
    Проверяем работоспособность схемы
    :return:
    """
    muscular = Muscular()
    muscular.context.strategy = StrategyBefore
    app = muscular()
    assert app == 'Strategy ApplyAdd Before String'

    muscular = Muscular()
    muscular.context.strategy = StrategyConext
    app = muscular()
    assert app == 'Strategy ApplyAdd Context String'

    muscular = Muscular()
    muscular.context.strategy = StrategyAfter
    app = muscular()
    assert app == 'Strategy ApplyAdd After String'

    muscular = Muscular()
    muscular.context.strategy = StrategyAllTrigger
    app = muscular()
    assert app == 'Strategy ApplyAdd Before StringAdd Context StringAdd After String'
