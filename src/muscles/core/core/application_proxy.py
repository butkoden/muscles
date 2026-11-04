from .application_context import get_application


class ApplicationProxy:

    def _get(self):
        application = get_application()

        if application is None:
            raise RuntimeError(
                "Application context is not initialized"
            )

        return application

    def __getattr__(self, name):
        return getattr(
            self._get(),
            name,
        )


application = ApplicationProxy()