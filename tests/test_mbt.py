"""Тесты RPC на основе модели."""

import threading

import pytest
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule

from src import model, server
from src.client import Client

STEPS = 30
EXAMPLES = 100

TIME = st.integers(min_value=0, max_value=2000000000)
TEXT = st.text(alphabet=st.characters(min_codepoint=32,
                                      max_codepoint=126), max_size=10)
MISSING = st.integers(min_value=-100, max_value=0)
INDEX = st.integers(min_value=1, max_value=20)


def start():
    instance = server.create("127.0.0.1", 0)
    threading.Thread(target=instance.serve_forever, daemon=True).start()
    return instance.server_address


ADDRESS = start()


class Expected:
    """Ожидаемое состояние."""

    def __init__(self):
        self.rows = {"participant": [], "command": [], "output": []}

    def add(self, table, fields):
        record = {"identifier": len(self.rows[table]) + 1}
        record.update(fields)
        self.rows[table].append(record)
        return dict(record)

    def all(self, table):
        return [dict(record) for record in self.rows[table]]

    def one(self, table, identifier):
        return dict(self.rows[table][identifier - 1])

    def select(self, moment):
        border = moment - model.SELECTION_WINDOW
        rows = []
        for participant in self.rows["participant"]:
            if participant["timestamp"] >= border:
                rows.extend(self.join(participant))
        return rows

    def join(self, participant):
        contents = [command["content"] for command in self.rows["command"]
                    if command["participant"] == participant["identifier"]]
        return [{"content": content,
                 "locale": participant["locale"],
                 "platform": participant["platform"]}
                for content in contents or [None]]


class RpcMachine(RuleBasedStateMachine):
    """Проверка RPC по эталону."""

    participants = Bundle("participants")
    commands = Bundle("commands")

    def __init__(self):
        super().__init__()
        model.reset()
        self.expected = Expected()
        self.client = Client(*ADDRESS)

    def teardown(self):
        self.client.close()

    @rule(target=participants, timestamp=TIME, locale=TEXT, platform=TEXT)
    def create_participant(self, timestamp, locale, platform):
        record = self.expected.add("participant", {
            "timestamp": timestamp, "locale": locale,
            "platform": platform})
        assert self.client.create_participant(
            timestamp, locale, platform) == record
        return record["identifier"]

    @rule()
    def get_participants(self):
        assert self.client.get_participants() == \
            self.expected.all("participant")

    @rule(identifier=participants)
    def get_participant(self, identifier):
        assert self.client.get_participant(identifier) == \
            self.expected.one("participant", identifier)

    @rule(target=commands, timestamp=TIME, content=TEXT,
          participant=participants, state=TEXT, enqueued=TIME)
    def create_command(self, timestamp, content, participant, state,
                       enqueued):
        record = self.expected.add("command", {
            "timestamp": timestamp, "content": content,
            "participant": participant, "state": state,
            "enqueued": enqueued})
        assert self.client.create_command(
            timestamp, content, participant, state, enqueued) == record
        return record["identifier"]

    @rule()
    def get_commands(self):
        assert self.client.get_commands() == self.expected.all("command")

    @rule(identifier=commands)
    def get_command(self, identifier):
        assert self.client.get_command(identifier) == \
            self.expected.one("command", identifier)

    @rule(timestamp=TIME, result=TEXT, state=TEXT, exception=TEXT,
          command=commands)
    def create_output(self, timestamp, result, state, exception, command):
        record = self.expected.add("output", {
            "timestamp": timestamp, "result": result, "state": state,
            "exception": exception, "command": command})
        assert self.client.create_output(
            timestamp, result, state, exception, command) == record

    @rule()
    def get_outputs(self):
        assert self.client.get_outputs() == self.expected.all("output")

    @rule(index=INDEX)
    def get_output(self, index):
        rows = self.expected.all("output")
        if index > len(rows):
            with pytest.raises(model.RecordNotFoundError):
                self.client.get_output(index)
        else:
            assert self.client.get_output(index) == rows[index - 1]

    @rule(moment=TIME)
    def select_recent_participant_commands(self, moment):
        assert self.client.select_recent_participant_commands(moment) == \
            self.expected.select(moment)

    @rule(identifier=MISSING)
    def missing_records(self, identifier):
        for read in (self.client.get_participant, self.client.get_command,
                     self.client.get_output):
            with pytest.raises(model.RecordNotFoundError):
                read(identifier)

    @rule(timestamp=TIME, locale=TIME, platform=TEXT)
    def wrong_type(self, timestamp, locale, platform):
        with pytest.raises(model.ValidationError):
            self.client.create_participant(timestamp, locale, platform)

    @rule(timestamp=TIME, content=TEXT, participant=MISSING, state=TEXT,
          enqueued=TIME)
    def broken_key(self, timestamp, content, participant, state, enqueued):
        with pytest.raises(model.ValidationError):
            self.client.create_command(timestamp, content, participant,
                                       state, enqueued)


RpcMachine.TestCase.settings = settings(max_examples=EXAMPLES,
                                        stateful_step_count=STEPS,
                                        deadline=None)

TestRpc = RpcMachine.TestCase
