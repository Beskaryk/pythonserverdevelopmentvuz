"""Клиент HTTP API."""

import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ApiError(Exception):
    """Ошибка HTTP API."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class Client:
    """Вызовы функций слоя данных через HTTP."""

    def __init__(self, base_url="http://127.0.0.1:5000", test_client=None):
        self.base_url = base_url.rstrip("/")
        self.test_client = test_client

    def create_participant(self, timestamp, locale, platform):
        return self._request("POST", "/core/api/participant-create", body={
            "timestamp": timestamp, "locale": locale, "platform": platform})

    def fetch_participants(self, **filters):
        return self._request("GET", "/core/api/participant-fetch",
                             query=filters)

    def inspect_participant(self, identifier):
        return self._request("GET", "/core/api/participant-inspect",
                             query={"identifier": identifier})

    def create_command(self, timestamp, content, participant, state,
                       enqueued):
        return self._request("POST", "/core/api/command-create", body={
            "timestamp": timestamp, "content": content,
            "participant": participant, "state": state,
            "enqueued": enqueued})

    def fetch_commands(self, participant, **filters):
        return self._request("GET", f"/core/api/command-fetch/{participant}",
                             query=filters)

    def inspect_command(self, identifier):
        return self._request("GET", "/core/api/command-inspect",
                             query={"identifier": identifier})

    def fetch_outputs(self, command, **filters):
        return self._request("GET", f"/core/api/output-fetch/{command}",
                             query=filters)

    def inspect_output(self, identifier):
        return self._request("GET", "/core/api/output-inspect",
                             query={"identifier": identifier})

    def fetch_report(self):
        return self._request("GET", "/core/api/report-fetch")

    def _request(self, method, path, query=None, body=None):
        headers = {"Accept": "application/json", "Accept-Language": "en"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if query:
            path += "?" + urlencode(query)
        if self.test_client is not None:
            response = self.test_client.open(path, method=method,
                                             headers=headers, json=body)
            return self._answer(response.status_code, response.get_json())
        data = json.dumps(body).encode() if body is not None else None
        request = Request(self.base_url + path, data=data,
                          headers=headers, method=method)
        try:
            with urlopen(request) as response:
                return self._answer(response.status, json.load(response))
        except HTTPError as exception:
            return self._answer(exception.code, json.load(exception))

    @staticmethod
    def _answer(status, body):
        if status >= 400:
            raise ApiError(status, body.get("error", "ошибка API"))
        return body
