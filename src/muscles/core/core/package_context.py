from contextvars import ContextVar


_current_package = ContextVar(
    "current_package",
    default=None,
)


def set_package(package):
    return _current_package.set(package)


def reset_package(token):
    _current_package.reset(token)


def get_package():
    return _current_package.get()