# Расширения пакетов

Расширения позволяют одному пакету предложить свою возможность другому пакету, даже если получатель будет установлен позже.

Например, `records` умеет загружать записи и проверять права на них. `storage` нужно узнать, можно ли показать файл, прикреплённый к записи. Чтобы `storage` не импортировал `records`, пакет `records` объявляет обработчик через общее расширение. Его получает `muscles-permissions`, а `storage` обращается к реестру permissions.

## Из чего состоит механизм

1. **Пакет-отправитель** возвращает `PackageExtension(target, value)` из метода `extensions()`.
2. **Muscles** сохраняет значение в реестре приложения под ключом `target`.
3. **Пакет-получатель** подписывается на этот ключ и получает все соответствующие значения.

`target` — строка, например `muscles.permissions.resources`. Она должна совпадать у отправителя и получателя. `value` — объявление, формат которого определяет получатель. Muscles не разбирает его содержимое.

## Пример

Здесь пакет `producer` передаёт строку, а пакет `consumer` собирает строки в собственный реестр. В реальном приложении вместо строки может передаваться объект обработчика.

```python
from muscles.core import (
    MusclesPackage,
    PackageExtension,
    PackageService,
    get_application_registry,
    install_package,
)


class HandlerRegistry:
    def __init__(self):
        self.handlers = []

    def register(self, handler):
        self.handlers.append(handler)


class ProducerPackage(MusclesPackage):
    namespace = "producer"

    def extensions(self, app, runtime):
        return [PackageExtension(
            target="example.handlers",
            value="обработчик",
        )]


class ConsumerPackage(MusclesPackage):
    namespace = "consumer"

    def services(self, app, runtime):
        handlers = HandlerRegistry()
        extensions = get_application_registry(app)
        extensions.subscribe_extensions("example.handlers", handlers.register)
        return [PackageService(HandlerRegistry, handlers)]


# app — заранее созданное приложение Muscles.
install_package(app, {}, ProducerPackage())
install_package(app, {}, ConsumerPackage())

handlers = app.container.resolve(HandlerRegistry)
assert handlers.handlers == ["обработчик"]
```

### Если отправитель установлен первым

1. `producer` объявляет расширение.
2. Muscles сохраняет его: подписчика пока нет.
3. `consumer` подписывается на `example.handlers`.
4. Muscles сразу передаёт ему сохранённое значение.

### Если получатель установлен первым

1. `consumer` подписывается на `example.handlers`.
2. `producer` объявляет расширение.
3. Muscles сразу передаёт значение подписчику.

Таким образом, результат не зависит от порядка установки этих пакетов. Доставка выполняется **синхронно** и в порядке регистрации значений.

## Если получатель отсутствует

Расширение остаётся в памяти и будет передано, если получатель подключится позже. Проверить расширения без подписчиков можно так:

```python
from muscles.core import doctor_application, get_application_registry

pending = get_application_registry(app).unhandled_extensions()
print(pending)  # Например: {"example.handlers": 1}

report = doctor_application(app)
print(report.get("unhandled_extensions", {}))
```

При наличии таких расширений диагностика возвращает `warning`, если другая проверка не обнаружила ошибку. Решение о том, считать ли отсутствие получателя ошибкой запуска, принимает приложение.

## Что нужно учитывать

- `extensions()` — необязательный hook; если его нет, пакет ничего не объявляет. Он может принимать нужные аргументы из `app`, `runtime`, `config`.
- Ключ должен быть непустой строкой. Используйте пространство имён владельца, чтобы разные пакеты не выбрали один ключ случайно.
- Проверку типа значения, повторной регистрации и бизнес-правил выполняет получатель.
- Подписчик вызывается сразу. Если он вызовет исключение, оно передаётся вызывающему коду; автоматического повтора и отката действий других подписчиков нет.
- Подписывайте получателя один раз. Отписка и удаление расширений пока не поддерживаются.
- Реестр принадлежит конкретному приложению и хранит значения в памяти. Передавайте через него объявления; соединения с БД и другие рабочие ресурсы размещайте в контейнере сервисов.

Пример для разрешений и вложений приведён в документации `muscles-permissions`.
