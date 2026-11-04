# muscles/core/core/module_loader.py

import importlib
import pkgutil


class ModuleLoader:

    def load_modules(self, modules):
        for module_name in modules:
            self._load_module(module_name)

    def _load_module(self, module_name):
        module = importlib.import_module(module_name)

        if not hasattr(module, "__path__"):
            return

        for module_info in pkgutil.iter_modules(module.__path__):
            self._load_module(
                f"{module_name}.{module_info.name}"
            )