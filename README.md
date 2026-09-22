# Практическая работа №1, вариант 5

## Этап 1. Модель данных

`src/model.py` хранит `Participant`, `Command` и `Output` в словарях.
`src/repl.py` позволяет вызывать десять функций модели вручную.

Локальный запуск:

```sh
python -m src.repl
```

## Этап 2. RPC поверх TCP

`src/protocol.py` описывает заголовки и XML-тела сообщений.
`src/server.py` принимает запросы, вызывает функции модели и ведёт журнал.
`src/client.py` предоставляет те же методы через TCP.

В первом терминале:

```sh
python -m src.server
```

Во втором терминале:

```sh
python -m src.repl --rpc
```

Адрес по умолчанию — `127.0.0.1:8765`. Его можно изменить параметрами
`--host` и `--port`. Эти параметры относятся только к этапу 2.

Пример команд REPL:

```text
create_participant 1000000 ru-RU windows
create_command 1000000 "SELECT 1" 1 queued 1000000
get_commands
exit
```
