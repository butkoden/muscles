# Muscles Core

`muscles.core` — базовый слой Muscles, который отвечает за создание приложения, подключение пакетов, конфигурацию, загрузку модулей и доступ к ресурсам приложения.

Главная идея проста:

> **Application владеет ресурсами приложения, Package собирает из них отдельную функциональность, а модули используют ресурсы через контекст.**

Это позволяет не связывать бизнес-код напрямую с конкретным способом запуска приложения.

---

# 1. Из чего состоит приложение

Типичное приложение на Muscles состоит из трёх уровней:

```text
Application
│
├── Configuration
│
├── Routes
├── API
├── Controllers
├── ...
│
└── Packages
    │
    ├── UsersPackage
    ├── AdminPackage
    └── CorePackage
```

### Application

`Application` — главный объект приложения.

Он владеет общими ресурсами:

- конфигурацией;
- маршрутизацией;
- API;
- контроллерами;
- подключенными пакетами;
- другими ресурсами приложения.

### Package

`Package` — самостоятельная функциональная часть приложения.

Например:

```text
UsersPackage
AdminPackage
PaymentsPackage
CorePackage
```

Package получает доступ к Application и может создать собственные ресурсы на его основе.

Например:

```text
Application.routes
       │
       └── UsersPackage.routes
```

При этом `UsersPackage` не создаёт отдельный сервер маршрутизации. Он использует маршрутизатор приложения, ограничивая его своим префиксом.

### Module

Module — обычный Python-модуль, в котором находится конкретная функциональность.

Например:

```text
packages/
└── users/
    ├── main.py
    ├── routes/
    │   ├── users.py
    │   └── profile.py
    └── api/
        └── users.py
```

---

# 2. Создание Application

Минимальное приложение выглядит примерно так:

```python
from muscles.core import App


class Application(App):

    modules = (
        "main.routes",
        "main.api",
    )


application = Application()
```

`modules` определяет модули, которые должны быть загружены при создании приложения.

Например:

```python
modules = (
    "main.routes",
    "main.api",
    "main.controllers",
)
```

Muscles загрузит указанные модули и их дочерние модули.

---

# 3. Ресурсы Application

Application обычно предоставляет общие ресурсы приложения.

Например:

```python
application.routes
application.api
application.controllers
application.config
```

Эти ресурсы создаются один раз на уровне Application и могут использоваться пакетами.

Например:

```python
class Application(App):

    def __init__(self):
        self.routes = Routes(...)
        self.api = RestApi(...)
        self.controllers = Controllers(...)

        super().__init__()
```

Конкретный набор ресурсов зависит от приложения.

Muscles Core не требует, чтобы у каждого приложения обязательно были `routes`, `api` или `controllers`.

Это принципиально:

> **Core предоставляет механизм композиции, а не навязывает структуру приложения.**

---

# 4. Конфигурация

Конфигурация подключается к Application.

Например:

```python
from muscles.core import App
from muscles.core import Configurator


class Application(App):

    config = Configurator(
        basedir="src",
        file="configs/configuration.yaml",
    )
```

Структура проекта:

```text
src/
├── app.py
├── configs/
│   └── configuration.yaml
└── main/
```

Пример конфигурации:

```yaml
packages:

  - class: packages.users.main.UsersPackage
    config:
      rootPath: /users
      apiPath: /api/v1/users

  - class: packages.admin.main.AdminPackage
    config:
      rootPath: /admin
```

После загрузки конфигурация становится доступна Application:

```python
application.config
```

---

# 5. Что такое Package

Package нужен для того, чтобы объединить связанную функциональность.

Например, вместо того чтобы регистрировать всё непосредственно в Application:

```python
application.routes.init(...)
application.api.init(...)
application.controllers.register(...)
```

можно создать:

```python
UsersPackage
```

который отвечает за весь Users-модуль.

Структура:

```text
packages/
└── users/
    ├── main.py
    ├── routes/
    └── api/
```

---

# 6. Создание Package

Package получает Application и свою конфигурацию.

Например:

```python
from muscles.core import MusclesPackage


class UsersPackage(MusclesPackage):

    modules = (
        "packages.users.routes",
        "packages.users.api",
    )

    def __init__(self, app, config):
        self.app = app
        self.config = config

        self.routes = app.routes.group(
            config.rootPath
        )

        self.api = app.api.group(
            config.apiPath
        )
```

Здесь происходит важная вещь.

Package не создаёт новый `Routes` или `RestApi`.

Он получает существующие ресурсы Application:

```text
Application
│
├── routes ────────────────┐
│                          ↓
│                    UsersPackage
│                          │
│                          └── routes
│
└── api ───────────────────┐
                           ↓
                       UsersPackage
                           │
                           └── api
```

Поэтому все маршруты остаются частью одного приложения.

---

# 7. Package и префиксы

Допустим, Application имеет:

```python
application.routes
```

Package получает:

```yaml
config:
  rootPath: /users
```

Тогда:

```python
self.routes = app.routes.group("/users")
```

создаёт группу маршрутов:

```text
Application
└── /users
    ├── /
    ├── /profile
    └── /settings
```

В модуле Package можно написать:

```python
from muscles.asgi import package_routes as routes


@routes.init("/")
async def home(request):
    ...
```

Фактический URL будет:

```text
/users/
```

Сам модуль при этом не обязан знать, какой `rootPath` ему назначил Package.

---

# 8. API

API работает по тому же принципу.

Application создаёт общий API:

```python
self.api = RestApi(
    prefix="/api/v1",
    ...
)
```

Package получает группу:

```python
self.api = app.api.group(
    "/users"
)
```

В результате:

```text
Application API
└── /api/v1
    └── /users
        ├── /
        ├── /profile
        └── /settings
```

Модуль Package работает только со своей группой:

```python
from muscles.asgi import package_api as api


@api.init("/", method="GET")
def users(request):
    ...
```

Фактический адрес:

```text
GET /api/v1/users/
```

---

# 9. Как модуль узнаёт свой Package

Muscles использует Package Context.

Когда Package загружает свои модули, Muscles устанавливает текущий Package:

```text
Package
   │
   ├── set current package
   │
   ├── load routes
   ├── load api
   ├── load controllers
   │
   └── reset package
```

Поэтому модуль может использовать:

```python
from muscles.asgi import package_routes as routes
```

и Muscles понимает, к какому Package относятся эти маршруты.

То есть модулю не нужно писать:

```python
package.routes.init(...)
```

и не нужно передавать Package вручную в каждый модуль.

---

# 10. Application Context

Аналогичный механизм существует для Application.

Во время загрузки и выполнения приложения Muscles знает текущий Application.

Поэтому можно использовать:

```python
from muscles import application
```

Например:

```python
from muscles import application


async def handler(request):
    return await application.template.render_async(
        "index.html"
    )
```

`application` здесь является не самим экземпляром Application, а прокси.

Прокси получает текущий Application из контекста.

Схематично:

```text
application
     │
     ↓
ApplicationProxy
     │
     ↓
current Application
```

Это позволяет модулям не получать Application через длинную цепочку аргументов.

---

# 11. Application Resources

Тот же принцип используется для отдельных ресурсов.

Например:

```python
from muscles.asgi import application_routes as routes
```

или:

```python
from muscles.asgi import application_api as api
```

Такие объекты являются прокси к ресурсам Application.

Например:

```text
application_routes
        │
        ↓
current Application
        │
        ↓
application.routes
```

А для Package:

```text
package_routes
        │
        ↓
current Package
        │
        ↓
package.routes
```

Таким образом, один и тот же модуль можно писать независимо от конкретного экземпляра Application или Package.

---

# 12. Загрузка модулей

Package определяет, какие модули ему принадлежат:

```python
class UsersPackage(MusclesPackage):

    modules = (
        "packages.users.routes",
        "packages.users.api",
    )
```

Muscles загружает их автоматически.

Например:

```text
packages.users.routes
│
├── users.py
├── profile.py
└── settings.py

packages.users.api
│
└── users.py
```

При загрузке:

```text
UsersPackage
    │
    ├── packages.users.routes
    │   ├── users
    │   ├── profile
    │   └── settings
    │
    └── packages.users.api
        └── users
```

Сам `ModuleLoader` не знает, что такое `routes` или `api`.

Для него это просто Python-модули.

Это важно, потому что Package может загружать что угодно:

```python
modules = (
    "packages.users.routes",
    "packages.users.api",
    "packages.users.admin",
    "packages.users.ai",
)
```

---

# 13. Как подключить Package

Packages подключаются через конфигурацию Application.

Например:

```yaml
packages:

  - class: packages.users.main.UsersPackage
    config:
      rootPath: /users
      apiPath: /api/v1/users
```

Application читает конфигурацию и создаёт Package:

```text
configuration.yaml
        │
        ↓
    Application
        │
        ↓
    UsersPackage
        │
        ├── routes
        ├── api
        └── modules
```

Package получает два аргумента:

```python
__init__(
    app,
    config,
)
```

где:

- `app` — Application;
- `config` — конфигурация конкретного Package.

---

# 14. Где создавать ресурсы

Хорошее правило:

### Application

Создаёт **общие ресурсы**:

```python
self.routes
self.api
self.config
self.database
self.cache
self.events
```

### Package

Создаёт **ресурсы своей области** на основе Application:

```python
self.routes = app.routes.group(...)
self.api = app.api.group(...)
```

### Module

Использует ресурсы Package:

```python
from muscles.asgi import package_routes as routes
```

Получается:

```text
Application
    │
    ├── global routes
    ├── global API
    ├── database
    └── config
          │
          ↓
       Package
          │
          ├── package routes
          ├── package API
          └── package config
                │
                ↓
             Modules
```

---

# 15. Что не следует делать

Не стоит создавать новый Application внутри Package:

```python
class UsersPackage:
    def __init__(self):
        self.app = App()  # ❌
```

Package должен использовать существующий Application:

```python
class UsersPackage:
    def __init__(self, app, config):
        self.app = app  # ✅
```

Не стоит создавать отдельный маршрутизатор без необходимости:

```python
self.routes = Routes()  # ❌
```

если Package должен быть частью маршрутизации Application.

Правильнее:

```python
self.routes = app.routes.group(
    config.rootPath
)
```

То же относится к API и другим ресурсам.

---

# 16. Главное правило архитектуры

В Muscles есть три уровня ответственности.

### Application

> **Я владею приложением и его общими ресурсами.**

### Package

> **Я собираю из этих ресурсов отдельную функциональную область.**

### Module

> **Я реализую конкретную функциональность этой области.**

В виде схемы:

```text
                  APPLICATION
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
        Routes         API        Database
          │            │            │
          └────────────┼────────────┘
                       ↓
                    PACKAGE
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Routes          API       Services
          │            │            │
          └────────────┼────────────┘
                       ↓
                    MODULES
```

Такой подход позволяет добавлять новые функциональные области, не изменяя ядро Application.

---

# 17. Минимальный пример

## Application

```python
from muscles.core import App, Configurator


class Application(App):

    config = Configurator(
        basedir="src",
        file="configs/configuration.yaml",
    )

    modules = (
        "main.routes",
        "main.api",
    )


application = Application()
```

## Configuration

```yaml
packages:

  - class: packages.users.main.UsersPackage
    config:
      rootPath: /users
      apiPath: /api/v1/users
```

## Package

```python
from muscles.core import MusclesPackage


class UsersPackage(MusclesPackage):

    modules = (
        "packages.users.routes",
        "packages.users.api",
    )

    def __init__(self, app, config):
        self.app = app
        self.config = config

        self.routes = app.routes.group(
            config.rootPath
        )

        self.api = app.api.group(
            config.apiPath
        )
```

## Route

```python
from muscles.asgi import package_routes as routes


@routes.init("/")
async def home(request):
    return "Users"
```

## API

```python
from muscles.asgi import package_api as api


@api.init("/", method="GET")
def users(request):
    return {
        "users": []
    }
```

При такой структуре Package остаётся самостоятельным, а Application продолжает управлять всеми общими ресурсами.

---

# 18. Коротко

Если нужно добавить новую функциональность:

**1. Создай Package**

```python
class UsersPackage(MusclesPackage):
    ...
```

**2. Получи нужные ресурсы Application**

```python
self.routes = app.routes.group(...)
self.api = app.api.group(...)
```

**3. Укажи модули Package**

```python
modules = (
    "packages.users.routes",
    "packages.users.api",
)
```

**4. Подключи Package в конфигурации**

```yaml
packages:
  - class: packages.users.main.UsersPackage
    config:
      rootPath: /users
```

**5. В модулях используй Package Resources**

```python
from muscles.asgi import package_routes as routes
```

или:

```python
from muscles.asgi import package_api as api
```

В результате Application остаётся владельцем инфраструктуры, Package — владельцем функциональной области, а модули содержат непосредственно код этой функциональности.