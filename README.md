# Практическая работа №1, вариант 5

## Этап 1. Модель данных

Данные `Participant`, `Command` и `Output` хранятся в словарях.
Реализованы создание, получение всех записей, получение записи по ID
и выборка команд участников за последние шесть минут.

`locale` — обязательное поле `Participant` из ER-диаграммы.

Запуск интерактивного режима:

```sh
python -m src.repl
```

Пример:

```text
create_participant 1000000 ru-RU windows
get_participants
create_command 1000000 "SELECT 1" 1 queued 1000000
select_recent_participant_commands 1000100
exit
```
