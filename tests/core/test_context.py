from .app.instance import App
from .app.instance import Strategy
from muscles.core.core import BaseStrategy, Context


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


class StrategyEntryContext(BaseStrategy):
    def execute(self, *args, **kwargs):
        return getattr(kwargs.get('entrypoint_context'), '_name', None)


class StrategyWithoutEntrypointContext(BaseStrategy):
    def execute(self, value, error_handler=None, container=None):
        return value


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


def test_context_passes_entrypoint_context_to_strategy():
    instance = App()
    instance.context.strategy = StrategyEntryContext
    result = instance()
    assert result == 'context'


def test_context_allows_legacy_dict_as_params_when_no_options_set():
    context = Context(Strategy1, {"entry": "point"})
    assert context.param("entry") == "point"
    assert context.transport is None


def test_context_keeps_compatibility_with_strategies_without_entrypoint_context():
    class _App:
        context = Context(StrategyWithoutEntrypointContext)

    app = _App()
    assert app.context.execute("ok") == "ok"
