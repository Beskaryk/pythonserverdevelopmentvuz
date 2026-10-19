"""HTTP API на Flask."""

import time
from pathlib import Path

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest

from .executor import execute
from .storage import (MemoryStore, RecordNotFoundError, StorageError,
                      ValidationError, parse_filters)

PARTICIPANT_INTS = {"identifier", "timestamp"}
COMMAND_INTS = {"identifier", "timestamp", "participant", "enqueued"}
OUTPUT_INTS = {"identifier", "timestamp", "command"}


def create_app(testing=False, store=None, clock=time.time):
    app = Flask(__name__)
    app.config.update(TESTING=testing, STORE=store or MemoryStore(),
                      CLOCK=clock,
                      RESULT_DIR=Path(__file__).parents[1] / "data/results")

    @app.before_request
    def check_headers():
        if request.method in {"POST", "PUT", "PATCH"} \
                and request.mimetype != "application/json":
            return error("Content-Type должен быть application/json", 415)
        if request.headers.get("Accept") != "application/json":
            return error("Accept должен быть application/json", 406)
        if request.headers.get("Accept-Language") != "en":
            return error("Accept-Language должен быть en", 406)
        return None

    @app.errorhandler(RecordNotFoundError)
    def not_found(exception):
        return error(str(exception), 404)

    @app.errorhandler(ValidationError)
    @app.errorhandler(BadRequest)
    def invalid(exception):
        return error(str(exception), 400)

    @app.post("/core/api/participant-create")
    def participant_create():
        body = json_body()
        return jsonify(data_store().create_participant(
            body.get("timestamp"), body.get("locale"), body.get("platform")))

    @app.get("/core/api/participant-fetch")
    def participant_fetch():
        filters = parse_filters(request.args, PARTICIPANT_INTS)
        return jsonify(data_store().fetch_participants(**filters))

    @app.get("/core/api/participant-inspect")
    def participant_inspect():
        identifier = required_identifier()
        return jsonify(data_store().inspect_participant(identifier))

    @app.post("/core/api/command-create")
    def command_create():
        body = json_body()
        command = data_store().create_command(
            body.get("timestamp"), body.get("content"),
            body.get("participant"), body.get("state"),
            body.get("enqueued"))
        execution = execute(command, app.config["RESULT_DIR"], testing)
        command = data_store().update_command_state(
            command["identifier"], execution["state"])
        output = data_store().create_output(
            int(app.config["CLOCK"]()), execution["result"],
            execution["state"], execution["exception"],
            command["identifier"])
        return jsonify({"command": command, "output": output})

    @app.get("/core/api/command-fetch/<int:participant>")
    def command_fetch(participant):
        filters = parse_filters(request.args, COMMAND_INTS)
        return jsonify(data_store().fetch_commands(participant, **filters))

    @app.get("/core/api/command-inspect")
    def command_inspect():
        return jsonify(data_store().inspect_command(required_identifier()))

    @app.get("/core/api/output-fetch/<int:command>")
    def output_fetch(command):
        filters = parse_filters(request.args, OUTPUT_INTS)
        return jsonify(data_store().fetch_outputs(command, **filters))

    @app.get("/core/api/output-inspect")
    def output_inspect():
        return jsonify(data_store().inspect_output(required_identifier()))

    @app.get("/core/api/report-fetch")
    def report_fetch():
        moment = int(app.config["CLOCK"]())
        return jsonify(data_store().fetch_report(moment))

    def data_store():
        return app.config["STORE"]

    return app


def json_body():
    body = request.get_json()
    if not isinstance(body, dict):
        raise ValidationError("ожидается объект JSON")
    return body


def required_identifier():
    if "identifier" not in request.args:
        raise ValidationError("не указан identifier")
    try:
        return int(request.args["identifier"])
    except ValueError as exception:
        raise ValidationError("identifier: ожидается int") from exception


def error(message, status):
    return jsonify({"error": message}), status
