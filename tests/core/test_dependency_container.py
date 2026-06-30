from muscles.core import DependencyContainer


class StoreInterface:
    pass


class Store(StoreInterface):
    pass


def test_dependency_container_reuses_app_scope_instances():
    container = DependencyContainer()
    container.register(StoreInterface, Store, scope="app")

    assert container.resolve(StoreInterface) is container.resolve(StoreInterface)


def test_dependency_container_keeps_request_scope_isolated():
    container = DependencyContainer()
    container.register(StoreInterface, Store, scope="request")
    first = container.create_scope()
    second = container.create_scope()

    assert first.resolve(StoreInterface) is first.resolve(StoreInterface)
    assert first.resolve(StoreInterface) is not second.resolve(StoreInterface)


def test_dependency_container_creates_transient_instances():
    container = DependencyContainer()
    container.register(StoreInterface, Store, scope="transient")

    assert container.resolve(StoreInterface) is not container.resolve(StoreInterface)
