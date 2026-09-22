"""Данные в памяти."""

import time

SELECTION_WINDOW = 360

PARTICIPANT = "Participant"
COMMAND = "Command"
OUTPUT = "Output"

_tables = {PARTICIPANT: {}, COMMAND: {}, OUTPUT: {}}
_counters = {PARTICIPANT: 0, COMMAND: 0, OUTPUT: 0}


class ModelError(Exception):
    """Ошибка модели."""


class ValidationError(ModelError):
    """Ошибка данных."""


class RecordNotFoundError(ModelError):
    """Запись не найдена."""


def reset():
    for table in _tables:
        _tables[table].clear()
        _counters[table] = 0


def create_participant(timestamp, locale, platform):
    return _insert(PARTICIPANT, {
        "timestamp": _as_int("timestamp", timestamp),
        "locale": _as_str("locale", locale),
        "platform": _as_str("platform", platform),
    })


def get_participants():
    return _all(PARTICIPANT)


def get_participant(identifier):
    return _one(PARTICIPANT, identifier)


def create_command(timestamp, content, participant, state, enqueued):
    return _insert(COMMAND, {
        "timestamp": _as_int("timestamp", timestamp),
        "content": _as_str("content", content),
        "participant": _as_key(PARTICIPANT, "participant", participant),
        "state": _as_str("state", state),
        "enqueued": _as_int("enqueued", enqueued),
    })


def get_commands():
    return _all(COMMAND)


def get_command(identifier):
    return _one(COMMAND, identifier)


def create_output(timestamp, result, state, exception, command):
    return _insert(OUTPUT, {
        "timestamp": _as_int("timestamp", timestamp),
        "result": _as_str("result", result),
        "state": _as_str("state", state),
        "exception": _as_str("exception", exception),
        "command": _as_key(COMMAND, "command", command),
    })


def get_outputs():
    return _all(OUTPUT)


def get_output(identifier):
    return _one(OUTPUT, identifier)


def select_recent_participant_commands(moment=None):
    if moment is None:
        moment = int(time.time())
    border = _as_int("moment", moment) - SELECTION_WINDOW
    rows = []
    for participant in _tables[PARTICIPANT].values():
        if participant["timestamp"] < border:
            continue
        rows.extend(_join(participant))
    return rows


def _join(participant):
    contents = [command["content"]
                for command in _tables[COMMAND].values()
                if command["participant"] == participant["identifier"]]
    return [{"content": content,
             "locale": participant["locale"],
             "platform": participant["platform"]}
            for content in contents or [None]]


def _insert(table, fields):
    _counters[table] += 1
    record = {"identifier": _counters[table]}
    record.update(fields)
    _tables[table][record["identifier"]] = record
    return dict(record)


def _one(table, identifier):
    key = _as_int("identifier", identifier)
    if key not in _tables[table]:
        raise RecordNotFoundError(f"{table}: записи {key} нет")
    return dict(_tables[table][key])


def _all(table):
    return [dict(record) for record in _tables[table].values()]


def _as_int(field, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{field}: ожидается int")
    return value


def _as_str(field, value):
    if not isinstance(value, str):
        raise ValidationError(f"{field}: ожидается str")
    return value


def _as_key(table, field, value):
    key = _as_int(field, value)
    if key not in _tables[table]:
        raise ValidationError(f"{field}: в {table} нет записи {key}")
    return key
