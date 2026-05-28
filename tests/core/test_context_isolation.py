from muscles.core.core import BaseStrategy, Context


class EchoStrategy(BaseStrategy):
    def execute(self, *args, **kwargs):
        return kwargs


def test_context_callbacks_and_params_are_instance_local():
    context_a = Context(EchoStrategy, params={'value': 'a'})
    context_b = Context(EchoStrategy, params={'value': 'b'})

    @context_a.before_start()
    def add_before(owner):
        context_a.set_param('before', 'only-a')

    result_a = context_a.execute()
    result_b = context_b.execute()

    assert result_a['value'] == 'a'
    assert result_a['before'] == 'only-a'
    assert result_b['value'] == 'b'
    assert 'before' not in result_b
    assert context_a.before_start_function_list != context_b.before_start_function_list
