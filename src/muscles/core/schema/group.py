from .schema import Schema


class BaseGroup(Schema):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self, "columns"):
            self.columns = []

    def dump(self) -> dict:
        results = super().dump()
        results_ = {}
        for child in self.columns:
            if callable(self.columns[child]):
                self.columns[child] = self.columns[child]()
            results_.update(self.columns[child].dump())
        results.update({
            self.__class__.__name__: {
                "type": "object",
                "properties": results_
            }
        })
        return results


class Group(BaseGroup):

    __metaclass__ = BaseGroup
    __prefix__ = ""
    __collection__ = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(kwargs) > 0 and hasattr(self, 'columns'):
            logger = getattr(self, "logger", None)
            for column in self.columns:
                self.columns[column].value = kwargs.get(column) or self.columns[column].default or None
                if logger is not None:
                    logger.debug("Group column value initialized", extra={"column": column})

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__()
