"""Проверки ответов RPC."""

import pytest

from src import protocol


def test_protocol_error_keeps_its_type():
    body = protocol.error_body(protocol.ProtocolError("неверная версия"))

    with pytest.raises(protocol.ProtocolError, match="неверная версия"):
        protocol.parse_response(body)


def test_unknown_response_status_is_protocol_error():
    body = b'<response status="unexpected"><str>text</str></response>'

    with pytest.raises(protocol.ProtocolError):
        protocol.parse_response(body)
