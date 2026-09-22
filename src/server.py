"""TCP-сервер RPC."""

import argparse
import logging
import socketserver
import sys

from . import model, protocol

log = logging.getLogger("rpc")

FUNCTIONS = {
    protocol.Operation.create_participant: model.create_participant,
    protocol.Operation.get_participants: model.get_participants,
    protocol.Operation.get_participant: model.get_participant,
    protocol.Operation.create_command: model.create_command,
    protocol.Operation.get_commands: model.get_commands,
    protocol.Operation.get_command: model.get_command,
    protocol.Operation.create_output: model.create_output,
    protocol.Operation.get_outputs: model.get_outputs,
    protocol.Operation.get_output: model.get_output,
    protocol.Operation.select_recent_participant_commands:
        model.select_recent_participant_commands,
}


def call(operation, arguments):
    try:
        return FUNCTIONS[operation](**arguments)
    except TypeError as error:
        raise model.ValidationError(f"неверные аргументы: {error}") from error


class Handler(socketserver.StreamRequestHandler):
    """Обслуживает одно TCP-соединение."""

    def handle(self):
        try:
            while True:
                header = self.rfile.read(protocol.REQUEST_HEADER)
                if len(header) != protocol.REQUEST_HEADER:
                    return
                self.serve(header)
        except OSError as error:
            log.info("соединение оборвано: %s", error)

    def serve(self, header):
        code = protocol.NO_CODE
        try:
            operation, size = protocol.decode_request_header(header)
            code = int(operation)
            arguments = protocol.parse_request(self.read_body(size))
            log.info("запрос %s %s", operation.name, arguments)
            body = protocol.result_body(call(operation, arguments))
        except (model.ModelError, protocol.ProtocolError) as error:
            log.info("ошибка %s: %s", type(error).__name__, error)
            body = protocol.error_body(error)
        log.info("ответ %s %s", code, body.decode())
        self.wfile.write(protocol.encode_response(code, body))

    def read_body(self, size):
        body = self.rfile.read(size)
        if len(body) != size:
            raise protocol.ProtocolError("тело запроса пришло не целиком")
        return body


class Server(socketserver.ThreadingTCPServer):
    """TCP-сервер RPC."""

    allow_reuse_address = True
    daemon_threads = True


def create(host=protocol.HOST, port=protocol.PORT):
    return Server((host, port), Handler)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=protocol.HOST)
    parser.add_argument("--port", type=int, default=protocol.PORT)
    options = parser.parse_args()
    logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                        format="%(asctime)s %(message)s")
    with create(options.host, options.port) as server:
        log.info("слушаю %s", server.server_address)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            log.info("остановлен")


if __name__ == "__main__":
    main()
