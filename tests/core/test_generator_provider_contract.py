from pathlib import Path

from muscles.core import GenerationRequest, GeneratorRegistry


class _FakeProvider:
    name = "fake"

    def supports(self, generator_type: str) -> bool:
        return generator_type in {"fake", "resource"}

    def generate(self, project_root: Path, request: GenerationRequest) -> list[str]:
        return [str(project_root / f"{request.name}.txt")]


def test_generator_registry_register_and_resolve():
    registry = GeneratorRegistry()
    provider = _FakeProvider()
    registry.register(provider)

    assert len(registry.providers()) == 1
    assert registry.resolve("fake") is provider


def test_generator_registry_ignores_duplicate_provider_names():
    registry = GeneratorRegistry()
    registry.register(_FakeProvider())
    registry.register(_FakeProvider())

    assert len(registry.providers()) == 1


def test_generator_registry_raises_for_unknown_generator_type():
    registry = GeneratorRegistry()
    registry.register(_FakeProvider())

    try:
        registry.resolve("unknown")
        assert False
    except ValueError as exc:
        assert "No generator provider" in str(exc)

