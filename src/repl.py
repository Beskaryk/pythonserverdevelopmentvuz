"""Интерактивный режим."""

import argparse
import shlex

from . import model, protocol
from .client import Client

HELP = """Команды:
  create_participant timestamp locale platform
  get_participants
  get_participant identifier
  create_command timestamp content participant state enqueued
  get_commands
  get_command identifier
  create_output timestamp result state exception command
  get_outputs
  get_output identifier
  select_recent_participant_commands [moment]
  help, exit
Число в кавычках передаётся как строка: "1" - строка, 1 - число."""

NAMES = ("create_participant", "get_participants", "get_participant",
         "create_command", "get_commands", "get_command",
         "create_output", "get_outputs", "get_output",
         "select_recent_participant_commands")

QUOTES = ("'", '"')
QUOTED_LENGTH = 2


def convert(token):
    if len(token) >= QUOTED_LENGTH and token[0] in QUOTES:
        return token.strip(token[0])
    if token == "null":
        return None
    try:
        return int(token)
    except ValueError:
        return token


def evaluate(target, line):
    try:
        parts = shlex.split(line, posix=False)
    except ValueError as error:
        return f"не разобрал строку: {error}"
    if not parts or parts[0] == "help":
        return HELP if parts else ""
    if parts[0] not in NAMES:
        return f"нет такой команды: {parts[0]}"
    try:
        return repr(getattr(target, parts[0])(
            *[convert(token) for token in parts[1:]]))
    except (model.ModelError, protocol.ProtocolError) as error:
        return f"{type(error).__name__}: {error}"
    except TypeError as error:
        return f"не тот набор аргументов: {error}"


def loop(target):
    print(HELP)
    while True:
        try:
            line = input(">>> ")
        except EOFError:
            return
        if line.strip() == "exit":
            return
        answer = evaluate(target, line)
        if answer:
            print(answer)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpc", action="store_true")
    parser.add_argument("--host", default=protocol.HOST)
    parser.add_argument("--port", type=int, default=protocol.PORT)
    options = parser.parse_args()
    if not options.rpc:
        loop(model)
        return
    with Client(options.host, options.port) as client:
        loop(client)


if __name__ == "__main__":
    main()
