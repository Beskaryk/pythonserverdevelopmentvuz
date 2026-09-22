"""Клиент RPC."""

import socket

from . import protocol


class Client:
    """Соединение с сервером."""

    def __init__(self, host=protocol.HOST, port=protocol.PORT):
        self.address = (host, port)
        self.socket = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, kind, value, traceback):
        self.close()

    def connect(self):
        if self.socket is None:
            self.socket = socket.create_connection(self.address)

    def close(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def create_participant(self, timestamp, locale, platform):
        return self.call(protocol.Operation.create_participant,
                         timestamp=timestamp, locale=locale,
                         platform=platform)

    def get_participants(self):
        return self.call(protocol.Operation.get_participants)

    def get_participant(self, identifier):
        return self.call(protocol.Operation.get_participant,
                         identifier=identifier)

    def create_command(self, timestamp, content, participant, state,
                       enqueued):
        return self.call(protocol.Operation.create_command,
                         timestamp=timestamp, content=content,
                         participant=participant, state=state,
                         enqueued=enqueued)

    def get_commands(self):
        return self.call(protocol.Operation.get_commands)

    def get_command(self, identifier):
        return self.call(protocol.Operation.get_command,
                         identifier=identifier)

    def create_output(self, timestamp, result, state, exception, command):
        return self.call(protocol.Operation.create_output,
                         timestamp=timestamp, result=result, state=state,
                         exception=exception, command=command)

    def get_outputs(self):
        return self.call(protocol.Operation.get_outputs)

    def get_output(self, identifier):
        return self.call(protocol.Operation.get_output,
                         identifier=identifier)

    def select_recent_participant_commands(self, moment=None):
        return self.call(
            protocol.Operation.select_recent_participant_commands,
            moment=moment)

    def call(self, operation, **arguments):
        self.connect()
        self.socket.sendall(protocol.encode_request(operation, arguments))
        size, _ = protocol.decode_response_header(
            self.receive(protocol.RESPONSE_HEADER))
        return protocol.parse_response(self.receive(size))

    def receive(self, size):
        data = bytearray()
        while len(data) < size:
            part = self.socket.recv(size - len(data))
            if not part:
                raise protocol.ProtocolError("сервер закрыл соединение")
            data += part
        return bytes(data)
