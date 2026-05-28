import os
import sys
from muscles.core.core import Context
from muscles.core.core import ApplicationMeta
from muscles.core.core import Configurator
from muscles.core.core import BaseStrategy

directory = os.path.dirname(__file__)
sys.path.append(f"{directory}")
sys.path.append(os.path.abspath(f"{directory}/.."))
sys.path.append(os.path.abspath(f"{directory}/../.."))


class Strategy(BaseStrategy):
    def execute(self, *args, **kwargs):
        return "Strategy Apply"


class Muscular(metaclass=ApplicationMeta):
    package_paths = []
    shutup = True

    config_file = 'config/configuration.yaml'

    config = Configurator(file=os.path.join(os.path.dirname(__file__), config_file),
                          basedir=os.path.dirname(os.path.realpath(__file__)))

    context = Context(Strategy, {})

    def __init__(self):
        self.init_auto_packages(self.config)
        self.init_imports(self.config.models)
        self.init_imports(self.config.api.controllers)

    @context.before_start()
    def before_start(self_context):
        self_context.context.set_param("before", "Add Before String")
        # print('>>>>>>>>>>>>before_start', self_context)
        pass

    @context.context()
    def apply_context(self_context, result):
        self_context.context.set_param("context", "Add Context String")
        # print('>>>>>>>>>>>>after_start', self_context, result)
        pass

    @context.after_start()
    def after_start(self_context, result):
        self_context.context.set_param("after", "Add After String")
        # print('>>>>>>>>>>>>after_start', self_context, result)
        pass

    def run(self, *args):
        return self.context.execute(*args, shutup=self.shutup)

    def __call__(self):
        return self.context.execute()


muscular = Muscular()
