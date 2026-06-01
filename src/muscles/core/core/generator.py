from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class GenerationRequest:
    generator_type: str
    name: str
    force: bool = False
    with_tests: bool = True


class GeneratorProvider(Protocol):
    name: str

    def supports(self, generator_type: str) -> bool:
        ...

    def generate(self, project_root: Path, request: GenerationRequest) -> list[str]:
        ...


class GeneratorRegistry:
    def __init__(self) -> None:
        self._providers: list[GeneratorProvider] = []

    def register(self, provider: GeneratorProvider) -> None:
        if any(item.name == provider.name for item in self._providers):
            return
        self._providers.append(provider)

    def providers(self) -> list[GeneratorProvider]:
        return list(self._providers)

    def resolve(self, generator_type: str) -> GeneratorProvider:
        for provider in self._providers:
            if provider.supports(generator_type):
                return provider
        raise ValueError(f"No generator provider for `{generator_type}`")

