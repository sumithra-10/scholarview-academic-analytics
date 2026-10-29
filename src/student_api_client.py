from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class StudentApiError(Exception):
    """Raised when the student records API cannot complete a request."""


def _request(
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, object] | None = None,
) -> object:
    url = f"{base_url.rstrip('/')}{path}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=body,
        method=method,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        body = error.read()
        error.close()
        try:
            response_body = json.loads(body.decode("utf-8"))
            message = response_body.get("error", error.reason)
        except (UnicodeDecodeError, json.JSONDecodeError):
            message = error.reason
        raise StudentApiError(f"Student API returned HTTP {error.code}: {message}") from error
    except (URLError, TimeoutError) as error:
        raise StudentApiError(f"Unable to reach the student API at {base_url}: {error}") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise StudentApiError("The student API returned an invalid JSON response.") from error


def list_students(base_url: str) -> list[dict[str, object]]:
    response = _request(base_url, "GET", "/students")
    if not isinstance(response, list) or not all(
        isinstance(student, dict) for student in response
    ):
        raise StudentApiError("The student API returned an invalid student list.")
    return response


def get_student(base_url: str, student_id: str) -> dict[str, object]:
    response = _request(base_url, "GET", f"/students/{quote(student_id, safe='')}")
    if not isinstance(response, dict):
        raise StudentApiError("The student API returned an invalid student record.")
    return response


def create_student(base_url: str, student: dict[str, object]) -> dict[str, object]:
    response = _request(base_url, "POST", "/students", student)
    if not isinstance(response, dict):
        raise StudentApiError("The student API returned an invalid student record.")
    return response


def update_student(
    base_url: str, student_id: str, student: dict[str, object]
) -> dict[str, object]:
    response = _request(
        base_url,
        "PUT",
        f"/students/{quote(student_id, safe='')}",
        student,
    )
    if not isinstance(response, dict):
        raise StudentApiError("The student API returned an invalid student record.")
    return response


def delete_student(base_url: str, student_id: str) -> None:
    _request(base_url, "DELETE", f"/students/{quote(student_id, safe='')}")
