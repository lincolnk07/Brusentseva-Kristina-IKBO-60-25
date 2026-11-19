# Визуализатор графа зависимостей NuGet

Учебный CLI-инструмент для анализа и визуализации зависимостей пакетов .NET
(NuGet). Сведения о NuGet читаются напрямую из V3 API и `.nupkg`; менеджер
пакетов и сторонние библиотеки для получения зависимостей не используются.
Для тестирования можно указать TOML-файл с графом, вершины которого названы
большими латинскими буквами.

## Требования

- Python 3.11 или новее.
- Для анализа реальных пакетов требуется доступ к NuGet V3 URL.
- Для проверки PEP 8 установите закреплённую версию инструмента через
  `make install-dev`.
- Для автоматических тестов используется встроенный модуль `unittest`.

Для получения реальных данных инструмент использует стандартные модули Python
`urllib`, `zipfile`, `xml.etree.ElementTree` и `tomllib`.

## Настройки

Параметры находятся в `config.toml`:

| Ключ | Назначение | Проверка |
| --- | --- | --- |
| `package_name` | Имя анализируемого пакета | Непустая строка; в тестовом режиме пакет должен быть в графе |
| `repository_url` | NuGet V3 URL или путь к TOML тестового графа | HTTP(S) URL или существующий файл в зависимости от режима |
| `test_repository` | Использовать локальный тестовый граф | Только `true` или `false` |
| `graph_file` | Имя выходного изображения | Непустое имя с расширением `.svg` |
| `ascii_tree` | Печатать ASCII-дерево на этапе 5 | Только `true` или `false` |
| `filter_substring` | Исключать имена, содержащие подстроку | Строка; пустая строка отключает фильтр |

Неизвестные и пропущенные ключи, пустые значения и неверные типы приводят к
понятному сообщению об ошибке. Для тестового графа путь разрешается относительно
текущего рабочего каталога.

## Этапы

Выбранный этап задаётся аргументом `--stage`. Конфигурация задаётся через
`--config`; оба параметра запуска не меняют перечень пользовательских настроек
из TOML.

```sh
./run.sh config.toml 1
./run.sh config.toml 2
./run.sh config.toml 3
./run.sh config.toml 4
./run.sh config.toml 5
```

1. **Минимальный прототип с конфигурацией.** Проверяет TOML и выводит каждую
   настройку в формате ключ-значение. Проверки охватывают все шесть полей.
2. **Сбор данных.** Извлекает прямые зависимости NuGet-пакета через NuGet V3;
   для выбранного этапа печатает прямые зависимости.
3. **Основные операции.** Рекурсивный DFS строит транзитивный граф, применяет
   фильтр и отмечает циклические рёбра. В тестовом режиме читается граф из файла.
4. **Дополнительные операции.** Печатает порядок обхода DFS постфиксно, то есть
   зависимости выводятся перед зависимыми от них пакетами. Для графа с циклом
   линейного порядка установки не существует; цикл выводится в stderr.
5. **Визуализация.** Сохраняет описание `PlantUML` рядом с SVG-файлом. Если
   `ascii_tree = true`, дополнительно печатает ASCII-дерево.

Для этапов 2–5 выберите тестовый граф в `config_test.toml`, затем запускайте
этапы по очереди:

```sh
./run.sh config_test.toml 2
./run.sh config_test.toml 3
./run.sh config_test.toml 4
./run.sh config_test.toml 5
```

`tests/fixtures/test_graph_cycle.toml` демонстрирует цикл `A → B → D → A` и
общую зависимость `D` у `B` и `C`. `test_graph_chain.toml` демонстрирует цепочку
без циклов. `config_chain.toml` запускает цепочку, а `config_filter.toml`
исключает пакет `B` из неё. Примеры этапов:

```sh
./run.sh config_chain.toml 3
./run.sh config_chain.toml 4
./run.sh config_chain.toml 5
./run.sh config_filter.toml 3
./run.sh config_filter.toml 5
```

## Тестовый формат репозитория

Каждый пакет записывается как ключ таблицы `[packages]`, а его прямые
зависимости — как список строк:

```toml
[packages]
A = ["B", "C"]
B = ["D"]
C = []
D = []
```

Имена пакетов тестового графа должны состоять из больших латинских букв. Все
ссылки на зависимости должны иметь соответствующие записи в `[packages]`.

## Примеры для трёх NuGet-пакетов

В `examples/` находятся готовые конфигурации трёх NuGet-пакетов. Запустите
этап 5 для каждого файла; программа создаст отдельные SVG-граф и PlantUML:

```sh
./run.sh examples/newtonsoft.toml 5
./run.sh examples/serilog.toml 5
./run.sh examples/nunit.toml 5
```

Результаты сохраняются в `output/` под разными именами.
Полные SVG и PlantUML создаются локально и не хранятся в Git. Ниже приведены
Mermaid-представления связей из графов программы; GitHub отображает их прямо
в README. Для получения полных изображений выполните команды выше.

### Newtonsoft.Json

```mermaid
graph LR
    Newtonsoft["Newtonsoft.Json"] --> CSharp["Microsoft.CSharp"]
    Newtonsoft --> NetStandard["NETStandard.Library"]
    Newtonsoft --> TypeConverter["System.ComponentModel.TypeConverter"]
    Newtonsoft --> Formatters["System.Runtime.Serialization.Formatters"]
    Newtonsoft --> Primitives["System.Runtime.Serialization.Primitives"]
    Newtonsoft --> XmlDocument["System.Xml.XmlDocument"]
```

### Serilog

```mermaid
graph LR
    Serilog --> DiagnosticSource["System.Diagnostics.DiagnosticSource"]
    Serilog --> Channels["System.Threading.Channels"]
    Serilog --> ValueTuple["System.ValueTuple"]
    DiagnosticSource --> Memory["System.Memory"]
    DiagnosticSource --> Unsafe["System.Runtime.CompilerServices.Unsafe"]
    Memory --> Buffers["System.Buffers"]
    Memory --> Vectors["System.Numerics.Vectors"]
    Memory --> Unsafe["System.Runtime.CompilerServices.Unsafe"]
    Channels --> AsyncInterfaces["Microsoft.Bcl.AsyncInterfaces"]
    Channels --> TasksExtensions["System.Threading.Tasks.Extensions"]
    AsyncInterfaces --> TasksExtensions
    TasksExtensions --> Unsafe
```

### NUnit

```mermaid
graph LR
    NUnit --> TasksExtensions["System.Threading.Tasks.Extensions"]
    NUnit --> ValueTuple["System.ValueTuple"]
    TasksExtensions --> Unsafe["System.Runtime.CompilerServices.Unsafe"]
```

## Функции проекта

Функции сгруппированы по модулям в `src/dependency_visualizer/`:

| Модуль | Функции и назначение |
| --- | --- |
| `config.py` | `Settings` хранит шесть настроек. `load_settings` читает TOML, проверяет состав ключей и вызывает проверку значений. `validate_settings` проверяет типы, расширение SVG, URL NuGet или наличие тестового файла. |
| `source.py` | `NuGetSource` получает сервисный индекс, выбирает последнюю стабильную версию, скачивает `.nupkg` и извлекает зависимости из `.nuspec`. Его методы `_find_package_base_url`, `_latest_version`, `_dependencies_for_version`, `_parse_nuspec`, `_get_json`, `_get_text` и `_get_bytes` выполняют соответствующие запросы и преобразования; `direct_dependencies` возвращает прямой список. `TestGraphSource` читает TOML граф; `_add_package` и `_validate_dependencies` проверяют его записи, а `direct_dependencies` возвращает список для узла. `compare_versions` и `version_numbers` сравнивают стабильные номера версий; `nuspec_from_archive` извлекает XML из архива пакета. |
| `graph.py` | `DependencyGraph` хранит корень, рёбра, циклы и постфиксный порядок DFS. `build_graph` строит транзитивный граф рекурсивно и применяет фильтр; его вложенная функция `visit` обходит вершины и отмечает циклы. `ascii_tree` формирует дерево; вложенная `append_children` печатает дочерние узлы и помечает повторное ребро цикла. |
| `render.py` | `plantuml_text` создаёт PlantUML, `save_plantuml` сохраняет файл, `save_svg` создаёт SVG. `node_id` формирует идентификатор PlantUML. `graph_levels` назначает уровни узлам; вложенная `visit` обходит рёбра. `layout_nodes` вычисляет координаты, `canvas_size` размер изображения, `svg_header` начало SVG, `edge_elements` рёбра, `arrow_marker` маркер стрелки, `node_elements` карточки пакетов и подписи. |
| `cli.py` | `parse_arguments` читает параметры запуска; `create_source` выбирает источник; `run_stage` запускает один из пяти этапов. `print_settings`, `print_direct_dependencies`, `print_graph`, `print_load_order`, `print_visualization`, `report_cycles` и `print_names` выводят данные этапов. `main` связывает загрузку конфигурации, запуск и сообщения об ошибках. |
| `__main__.py` | Запускает `main`, когда модуль вызывается через `python -m dependency_visualizer`. |

## Автоматические проверки

Создайте виртуальное окружение, установите закреплённую версию `pycodestyle`,
затем запустите модульные тесты и проверку PEP 8:

```sh
python3 -m venv .venv
. .venv/bin/activate
make install-dev
make test
make lint
```

Тесты проверяют шесть параметров конфигурации и их ошибки, транзитивный DFS,
фильтр, порядок, циклы, TOML тестового репозитория, сравнение версий NuGet,
извлечение `.nuspec`, PlantUML и разбор созданного SVG.

## Сравнение со штатным графом NuGet

Проверка выполнена 20 ноября 2026 года с .NET SDK 11.0.100 и `net8.0`.
`dotnet nuget why` выводит граф зависимостей пакета для выбранного проекта и
целевой платформы ([документация Microsoft](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-nuget-why)).
Версии пакетов зафиксированы в команде воспроизведения и соответствуют
последним стабильным на дату проверки.

| Пакет | Версия | Узлов/рёбер приложения | Прямые рёбра обобщённого графа | `dotnet nuget why` для `net8.0` |
| --- | --- | ---: | --- | --- |
| `Newtonsoft.Json` | `13.0.4` | 96 / 518 | `Microsoft.CSharp`, `NETStandard.Library`, `System.ComponentModel.TypeConverter`, `System.Runtime.Serialization.Formatters`, `System.Runtime.Serialization.Primitives`, `System.Xml.XmlDocument` | Только `Newtonsoft.Json@13.0.4`; `NETStandard.Library` не входит в восстановленный граф |
| `Serilog` | `4.4.0` | 10 / 12 | `System.Diagnostics.DiagnosticSource`, `System.Threading.Channels`, `System.ValueTuple` | Только `Serilog@4.4.0`; `System.Diagnostics.DiagnosticSource` не входит в восстановленный граф |
| `NUnit` | `5.0.0` | 4 / 3 | `System.Threading.Tasks.Extensions`, `System.ValueTuple` | Только `NUnit@5.0.0`; `System.Threading.Tasks.Extensions` не входит в восстановленный граф |

Полное сравнение воспроизводится скриптом. Нужен .NET SDK 8.0.4xx или новее;
скрипт создаёт временные проекты, восстанавливает выбранные версии и вызывает
штатную команду для корневого пакета и одного объявленного дочернего пакета:

```sh
./scripts/compare_nuget.sh
```

В каждом примере штатный граф `net8.0` содержит только верхнеуровневый пакет;
проверка его прямого дочернего пакета завершается сообщением «нет зависимости».
Обобщённый граф приложения показывает дополнительные связи, объявленные в
других группах `.nuspec`. Результаты различаются потому, что NuGet выбирает
совместимую с целевой платформой группу и разрешает ограничения версий, а
приложение собирает идентификаторы зависимостей из всех групп.

Порядок этапа 4 — постфиксный DFS по объявленным рёбрам. Он не заявляется как
порядок восстановления или загрузки пакетов NuGet.

## Семантика графа NuGet

Граф реального NuGet-пакета обозначает **обобщённый граф объявленных
зависимостей**: для последней стабильной версии каждого пакета объединяются
связи из всех групп `.nuspec`. Версионные ограничения и целевые платформы не
разрешаются. Поэтому SVG не следует трактовать как результат `restore` для
конкретного проекта и framework. В CLI эта семантика также печатается при
построении реального графа. Такой режим соответствует имеющимся шести
настройкам: отдельного параметра целевой платформы среди них нет.

## Проверка сообщений Git-коммитов

С6 проверяется для истории этой практической работы — от базового коммита
`a0c8ba2` до текущего `HEAD`:

```sh
./scripts/check_scoped_commits.sh a0c8ba2 HEAD
```

Опубликованные ранее коммиты предыдущей практической работы не входят в эту
область проверки и не переписываются.

## Структура проекта

```text
.
├── config.toml
├── config_chain.toml
├── config_filter.toml
├── config_test.toml
├── examples/
├── Makefile
├── README.md
├── requirements-dev.txt
├── run.sh
├── scripts/
│   ├── check_scoped_commits.sh
│   └── compare_nuget.sh
├── src/
│   └── dependency_visualizer/
└── tests/
    ├── fixtures/
    ├── test_config.py
    ├── test_graph.py
    └── test_source_render.py
```

Запуск из корня проекта: `./run.sh [файл.toml] [этап 1–5]`. Либо
`make run` запускает этап 5 с `config.toml`. Внешние Python-пакеты для работы
программы не требуются.
