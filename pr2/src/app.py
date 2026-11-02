"""HTTP API на Flask."""

import time
from pathlib import Path

from flask import Flask, jsonify, request
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from werkzeug.exceptions import BadRequest

from .executor import execute
from .schemas import (CommandCreate, CommandFilters, IdentifierQuery,
                      OutputFilters, ParticipantCreate, ParticipantFilters)
from .storage import MemoryStore, RecordNotFoundError, ValidationError


def create_app(testing=False, store=None, clock=time.time):
    app = Flask(__name__)
    app.config.update(TESTING=testing,
                      STORE=store or MemoryStore(),
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

    @app.errorhandler(PydanticValidationError)
    def schema_invalid(exception):
        return error("неверные входные данные", 400)

    @app.post("/core/api/participant-create")
    def participant_create():
        body = json_body(ParticipantCreate)
        return jsonify(data_store().create_participant(
            body.timestamp, body.locale, body.platform))

    @app.get("/core/api/participant-fetch")
    def participant_fetch():
        filters = query_values(ParticipantFilters)
        return jsonify(data_store().fetch_participants(**filters))

    @app.get("/core/api/participant-inspect")
    def participant_inspect():
        identifier = required_identifier()
        return jsonify(data_store().inspect_participant(identifier))

    @app.post("/core/api/command-create")
    def command_create():
        body = json_body(CommandCreate)
        command = data_store().create_command(
            body.timestamp, body.content, body.participant, body.state,
            body.enqueued)
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
        filters = query_values(CommandFilters)
        return jsonify(data_store().fetch_commands(participant, **filters))

    @app.get("/core/api/command-inspect")
    def command_inspect():
        return jsonify(data_store().inspect_command(required_identifier()))

    @app.get("/core/api/output-fetch/<int:command>")
    def output_fetch(command):
        filters = query_values(OutputFilters)
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


def json_body(model):
    return model.model_validate(request.get_json())


def query_values(model: type[BaseModel]):
    values = model.model_validate(request.args.to_dict())
    return values.model_dump(exclude_none=True)


def required_identifier():
    values = IdentifierQuery.model_validate(request.args.to_dict())
    return values.identifier


def error(message, status):
    return jsonify({"error": message}), status
