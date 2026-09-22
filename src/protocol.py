"""Формат сообщений RPC."""

from enum import IntEnum
from xml.etree import ElementTree

from . import model

VERSION = 1
ORDER = "little"
ENCODING = "utf-8"

VERSION_SIZE = 1
REQUEST_CODE_SIZE = 2
REQUEST_SIZE_SIZE = 5
REQUEST_HEADER = 8
RESPONSE_SIZE_SIZE = 4
RESPONSE_CODE_SIZE = 1
RESPONSE_HEADER = 5

CODE_AT = 1
SIZE_AT = 3
RESPONSE_CODE_AT = 4

MAX_BODY = 1048576
NO_CODE = 0
ONE_CHILD = 1

HOST = "127.0.0.1"
PORT = 8765


class ProtocolError(Exception):
    """Ошибка протокола."""


ERRORS = {
    "ValidationError": model.ValidationError,
    "RecordNotFoundError": model.RecordNotFoundError,
    "ProtocolError": ProtocolError,
}


class Operation(IntEnum):
    """Коды операций RPC."""

    create_participant = 1
    get_participants = 2
    get_participant = 3
    create_command = 4
    get_commands = 5
    get_command = 6
    create_output = 7
    get_outputs = 8
    get_output = 9
    select_recent_participant_commands = 10


def encode_request(operation, arguments):
    body = _serialize(_arguments_element(arguments))
    frame = VERSION.to_bytes(VERSION_SIZE, ORDER)
    frame += int(operation).to_bytes(REQUEST_CODE_SIZE, ORDER)
    frame += len(body).to_bytes(REQUEST_SIZE_SIZE, ORDER)
    return frame + body


def decode_request_header(header):
    if len(header) != REQUEST_HEADER:
        raise ProtocolError("короткий заголовок запроса")
    version = int.from_bytes(header[:VERSION_SIZE], ORDER)
    if version != VERSION:
        raise ProtocolError(f"версия {version} не поддерживается")
    code = int.from_bytes(header[CODE_AT:SIZE_AT], ORDER)
    size = int.from_bytes(header[SIZE_AT:REQUEST_HEADER], ORDER)
    if size > MAX_BODY:
        raise ProtocolError("слишком большое тело запроса")
    try:
        return Operation(code), size
    except ValueError as error:
        raise ProtocolError(f"неизвестный код операции {code}") from error


def encode_response(code, body):
    frame = len(body).to_bytes(RESPONSE_SIZE_SIZE, ORDER)
    frame += int(code).to_bytes(RESPONSE_CODE_SIZE, ORDER)
    return frame + body


def decode_response_header(header):
    if len(header) != RESPONSE_HEADER:
        raise ProtocolError("короткий заголовок ответа")
    size = int.from_bytes(header[:RESPONSE_SIZE_SIZE], ORDER)
    code = int.from_bytes(header[RESPONSE_CODE_AT:RESPONSE_HEADER], ORDER)
    if size > MAX_BODY:
        raise ProtocolError("слишком большое тело ответа")
    return size, code


def parse_request(body):
    root = _parse(body)
    if root.tag != "request":
        raise ProtocolError("корень запроса должен быть request")
    return {_name(item): _decode(item[0]) for item in root}


def result_body(value):
    root = ElementTree.Element("response", {"status": "ok"})
    root.append(_encode(value))
    return _serialize(root)


def error_body(error):
    root = ElementTree.Element(
        "response", {"status": "error", "type": type(error).__name__})
    root.append(_encode(str(error)))
    return _serialize(root)


def parse_response(body):
    root = _parse(body)
    if root.tag != "response" or len(root) != ONE_CHILD:
        raise ProtocolError("неверная структура ответа")
    value = _decode(root[0])
    if root.get("status") == "ok":
        return value
    if root.get("status") != "error" or root.get("type") not in ERRORS:
        raise ProtocolError("неверный статус или тип ошибки ответа")
    raise ERRORS[root.get("type")](value)


def _arguments_element(arguments):
    root = ElementTree.Element("request")
    for name, value in arguments.items():
        item = ElementTree.SubElement(root, "argument", {"name": name})
        item.append(_encode(value))
    return root


def _name(item):
    name = item.get("name")
    if name is None or len(item) != ONE_CHILD:
        raise ProtocolError("неверное описание аргумента")
    return name


def _encode(value):
    if value is None:
        return ElementTree.Element("null")
    if isinstance(value, int):
        return _text_element("int", str(value))
    if isinstance(value, str):
        return _text_element("str", value)
    if isinstance(value, list):
        element = ElementTree.Element("list")
        element.extend(_encode(item) for item in value)
        return element
    element = ElementTree.Element("dict")
    for key, item in value.items():
        entry = ElementTree.SubElement(element, "entry", {"key": key})
        entry.append(_encode(item))
    return element


def _decode(element):
    if element.tag == "null":
        return None
    if element.tag == "int":
        return _decode_int(element)
    if element.tag == "str":
        return element.text or ""
    if element.tag == "list":
        return [_decode(item) for item in element]
    if element.tag == "dict":
        return {item.get("key"): _decode(item[0]) for item in element}
    raise ProtocolError(f"неизвестный тег {element.tag}")


def _decode_int(element):
    try:
        return int(element.text or "")
    except ValueError as error:
        raise ProtocolError("неверное значение int") from error


def _text_element(tag, text):
    element = ElementTree.Element(tag)
    element.text = text
    return element


def _serialize(element):
    return ElementTree.tostring(element, encoding=ENCODING,
                                xml_declaration=False)


def _parse(body):
    try:
        return ElementTree.fromstring(body.decode(ENCODING))
    except (ElementTree.ParseError, UnicodeDecodeError) as error:
        raise ProtocolError("тело не является XML") from error
