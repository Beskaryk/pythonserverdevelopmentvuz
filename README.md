# Практическая работа №1, вариант 5

Прототип веб-приложения с RPC поверх TCP. Данные держатся в памяти,
на диск ничего не пишется. Python 3.10+, для самой работы прототипа
сторонние библиотеки не нужны, они нужны только для тестов.

```
src/model.py      модель слоя доступа к данным (этап 1)
src/repl.py       REPL (этап 1)
src/protocol.py   кадры и тела сообщений RPC (этап 2)
src/server.py     сервер RPC поверх TCP (этап 2)
src/client.py     клиент RPC (этап 2)
tests/test_mbt.py тесты на основе модели (этап 3)
```

## Функции и настройки

Записи таблиц — словари. Идентификаторы выдаются по порядку с 1,
у каждой таблицы свой счётчик. Для `Command.participant` и
`Output.command` проверяется, что запись, на которую ссылаются,
существует.

Всего 10 функций, они же 10 операций RPC:

| Код | Функция |
|----|---------|
| 1 | `create_participant(timestamp, locale, platform)` |
| 2 | `get_participants()` |
| 3 | `get_participant(identifier)` |
| 4 | `create_command(timestamp, content, participant, state, enqueued)` |
| 5 | `get_commands()` |
| 6 | `get_command(identifier)` |
| 7 | `create_output(timestamp, result, state, exception, command)` |
| 8 | `get_outputs()` |
| 9 | `get_output(identifier)` |
| 10 | `select_recent_participant_commands(moment=None)` |

Последняя реализует формулу

```
PROJECT[C.content, P.locale, P.platform](
    SELECT[P.timestamp >= now - 6 min](
        P LEFT JOIN[P.identifier = C.participant] C))
```

Левое внешнее соединение оставляет всех участников, поэтому у
участника без команд в строке будет `content = None`. Аргумент
`moment` задаёт `now` в секундах (если не передан — текущее время),
он нужен, чтобы результат не зависел от часов при тестах.

Ошибки: `ValidationError` (не тот тип атрибута или битый внешний
ключ), `RecordNotFoundError` (нет записи), `ProtocolError` (кадр или
тело не по спецификации). Клиент поднимает исключение того же класса,
что и сервер.

Кадры по табл. 5, порядок байт от младшего к старшему. Запрос:
версия — 1 байт, код операции — 2 байта, размер тела — 5 байт, дальше
тело XML. Ответ: размер тела — 4 байта, код операции — 1 байт, дальше
тело XML. Если версия или код операции неверные, в ответе код 0.

Тело запроса и ответа:

```xml
<request><argument name="identifier"><int>1</int></argument></request>
<response status="ok"><dict>...</dict></response>
<response status="error" type="RecordNotFoundError"><str>...</str></response>
```

Тип значения — это имя тега: `null`, `int`, `str`, `list`, `dict`.

Настройки: `--host` и `--port` у сервера и у REPL (по умолчанию
127.0.0.1:8765), окно выборки — `model.SELECTION_WINDOW` (360 секунд),
версия протокола — `protocol.VERSION`.

## Сборка и запуск

Отдельного шага сборки нет: Python не компилируется, прототип работает
на стандартной библиотеке. Подготовка сводится к созданию виртуального
окружения и установке зависимостей, которые нужны только тестам.

```sh
python -m venv .venv
. .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Запуск:

```sh
make server     # сервер RPC
make repl       # REPL поверх модели
make client     # REPL поверх RPC (сервер должен быть запущен)
make test       # тесты
make coverage   # покрытие по ветвям
```

Без make:

```sh
python -m src.server --port 8765
python -m src.repl
python -m src.repl --rpc --port 8765
python -m pytest tests
python -m coverage run --branch --source=src -m pytest tests
python -m coverage report -m
```

## Примеры

REPL поверх модели:

```
>>> create_participant 1000000 ru-RU linux
{'identifier': 1, 'timestamp': 1000000, 'locale': 'ru-RU', 'platform': 'linux'}
>>> create_command 1000000 "SELECT 1" 1 queued 1000000
{'identifier': 1, 'timestamp': 1000000, 'content': 'SELECT 1', ...}
>>> select_recent_participant_commands 1000100
[{'content': 'SELECT 1', 'locale': 'ru-RU', 'platform': 'linux'}]
>>> get_command 9
RecordNotFoundError: Command: записи 9 нет
>>> create_participant abc ru-RU linux
ValidationError: timestamp: ожидается int
>>> exit
```

То же самое через RPC — `make client`, команды те же.

Журнал сервера:

```
запрос create_participant {'timestamp': 1000000, 'locale': 'ru-RU', ...}
ответ 1 <response status="ok"><dict><entry key="identifier">...
ошибка RecordNotFoundError: Participant: записи 42 нет
```

Клиент из кода:

```python
from src.client import Client

with Client("127.0.0.1", 8765) as client:
    participant = client.create_participant(1000000, "ru-RU", "linux")
    client.create_command(1000000, "SELECT 1",
                          participant["identifier"], "queued", 1000000)
    print(client.select_recent_participant_commands(1000100))
```

## Тесты

`tests/test_mbt.py` — машина состояний на `RuleBasedStateMachine`.
Класс `Expected` — упрощённая модель на списках, она написана отдельно
от рабочего кода. Hypothesis сама генерирует последовательности
вызовов, после каждого вызова результат сравнивается с эталоном.
Задействованы все 10 методов RPC плюс ошибочные сценарии (нет записи,
не тот тип атрибута, битый внешний ключ). Покрытие по ветвям —
`make coverage`.
