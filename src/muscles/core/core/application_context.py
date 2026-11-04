from contextvars import ContextVar


_current_application = ContextVar(
    "current_application",
    default=None,
)


def set_application(application):
    return _current_application.set(application)


def reset_application(token):
    _current_application.reset(token)


def get_application():
    return _current_application.get()