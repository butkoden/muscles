from __future__ import annotations

from abc import ABC
from typing import Any, List, Optional


class Schema(ABC):

    registry = []

    def __init__(self, *args, **kwargs):
        self._parent: Optional[Schema] = None
        self._children: List[Schema] = []
        for arg in args:
            if isinstance(arg, Schema):
                self._children.append(arg)

    def __getstate__(self):
        return self.state

    def __setstate__(self, state):
        self.state = self.dump()

    def __set_name__(self, owner, name):
        owner._children.append(self)

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__()
        cls.registry.append(cls)

    @property
    def parent(self) -> Optional[Schema]:
        return self._parent

    @parent.setter
    def parent(self, parent: Optional[Schema]):
        self._parent = parent

    def add(self, schema: Schema) -> None:
        self._children.append(schema)

    def remove(self, schema: Schema) -> None:
        if schema in self._children:
            self._children.remove(schema)

    def is_composite(self) -> bool:
        return True

    def dump(self) -> dict:
        results = []
        for child in self._children:
            results.append(child.dump())
        return {
            "class": self.__class__.__name__,
            "children": results
        }

    def to_json(self) -> Any:
        results = []
        for child in self._children:
            results.append(child.to_json())
        return results
