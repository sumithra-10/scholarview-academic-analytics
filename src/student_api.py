from __future__ import annotations

import csv
import json
import math
import os
import sqlite3
from collections.abc import Mapping
from contextlib import contextmanager
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = ROOT / "data" / "student_records.sqlite3"
DEFAULT_SEED_PATH = ROOT / "data" / "cleaned_student_data.csv"
REQUIRED_FIELDS = (
    "Student_ID",
    "Attendance_Percent",
    "Study_Hours_Per_Week",
    "Subject_Math",
    "Subject_Python",
    "Subject_DBMS",
    "Subject_AI",
)
OPTIONAL_FIELDS = (
    "Assignment_Score",
    "Internal_Marks",
    "Participation_Score",
    "Previous_Semester_Score",
)
NUMERIC_FIELDS = REQUIRED_FIELDS[1:] + OPTIONAL_FIELDS
SCORE_FIELDS = (
    "Attendance_Percent",
    "Subject_Math",
    "Subject_Python",
    "Subject_DBMS",
    "Subject_AI",
    *OPTIONAL_FIELDS,
)
ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS


class StudentNotFoundError(Exception):
    pass


class StudentAlreadyExistsError(Exception):
    pass


class InvalidStudentError(ValueError):
    pass


def normalize_student(payload: Mapping[str, Any]) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        raise InvalidStudentError("A student record must be a JSON object.")

    unknown_fields = set(payload) - set(ALL_FIELDS)
    if unknown_fields:
        raise InvalidStudentError(
            "Unknown fields: " + ", ".join(sorted(unknown_fields))
        )

    missing_fields = set(REQUIRED_FIELDS) - set(payload)
    if missing_fields:
        raise InvalidStudentError(
            "Missing required fields: " + ", ".join(sorted(missing_fields))
        )

    student_id = payload["Student_ID"]
    if not isinstance(student_id, str) or not student_id.strip():
        raise InvalidStudentError("Student_ID must be a non-empty string.")
    student_id = student_id.strip()
    if len(student_id) > 100:
        raise InvalidStudentError("Student_ID cannot exceed 100 characters.")

    student: dict[str, object] = {"Student_ID": student_id}
    for field in NUMERIC_FIELDS:
        value = payload.get(field)
        if value is None and field in OPTIONAL_FIELDS:
            student[field] = None
            continue
        if isinstance(value, bool):
            raise InvalidStudentError(f"{field} must be a number.")
        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise InvalidStudentError(f"{field} must be a number.") from error
        if not math.isfinite(number):
            raise InvalidStudentError(f"{field} must be a finite number.")
        if field in SCORE_FIELDS and not 0 <= number <= 100:
            raise InvalidStudentError(f"{field} must be between 0 and 100.")
        if field == "Study_Hours_Per_Week" and number < 0:
            raise InvalidStudentError("Study_Hours_Per_Week cannot be negative.")
        student[field] = number
    return student


class StudentStore:
    def __init__(
        self,
        database_path: str | Path = DEFAULT_DATABASE_PATH,
        seed_path: str | Path | None = DEFAULT_SEED_PATH,
    ) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize(seed_path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self, seed_path: str | Path | None) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    Student_ID TEXT PRIMARY KEY,
                    Attendance_Percent REAL NOT NULL,
                    Study_Hours_Per_Week REAL NOT NULL,
                    Subject_Math REAL NOT NULL,
                    Subject_Python REAL NOT NULL,
                    Subject_DBMS REAL NOT NULL,
                    Subject_AI REAL NOT NULL,
                    Assignment_Score REAL,
                    Internal_Marks REAL,
                    Participation_Score REAL,
                    Previous_Semester_Score REAL
                )
                """
            )
            has_students = connection.execute(
                "SELECT EXISTS(SELECT 1 FROM students)"
            ).fetchone()[0]

        if not has_students and seed_path is not None:
            self.seed_from_csv(seed_path)

    def seed_from_csv(self, csv_path: str | Path) -> None:
        with Path(csv_path).open(encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                self.create_student(row)

    def list_students(self) -> list[dict[str, object]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM students ORDER BY Student_ID"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_student(self, student_id: str) -> dict[str, object]:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM students WHERE Student_ID = ?", (student_id,)
            ).fetchone()
        if row is None:
            raise StudentNotFoundError(f"Student {student_id!r} was not found.")
        return dict(row)

    def create_student(self, payload: Mapping[str, Any]) -> dict[str, object]:
        student = normalize_student(payload)
        columns = ", ".join(ALL_FIELDS)
        placeholders = ", ".join("?" for _ in ALL_FIELDS)
        values = tuple(student[field] for field in ALL_FIELDS)
        try:
            with self._connection() as connection:
                connection.execute(
                    f"INSERT INTO students ({columns}) VALUES ({placeholders})",
                    values,
                )
        except sqlite3.IntegrityError as error:
            raise StudentAlreadyExistsError(
                f"Student {student['Student_ID']!r} already exists."
            ) from error
        return self.get_student(str(student["Student_ID"]))

    def update_student(
        self, student_id: str, payload: Mapping[str, Any]
    ) -> dict[str, object]:
        record = dict(payload)
        if "Student_ID" in record and record["Student_ID"] != student_id:
            raise InvalidStudentError("Student_ID cannot be changed.")
        record["Student_ID"] = student_id
        student = normalize_student(record)
        assignments = ", ".join(f"{field} = ?" for field in ALL_FIELDS[1:])
        values = tuple(student[field] for field in ALL_FIELDS[1:]) + (student_id,)
        with self._connection() as connection:
            cursor = connection.execute(
                f"UPDATE students SET {assignments} WHERE Student_ID = ?",
                values,
            )
        if cursor.rowcount == 0:
            raise StudentNotFoundError(f"Student {student_id!r} was not found.")
        return self.get_student(student_id)

    def delete_student(self, student_id: str) -> None:
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM students WHERE Student_ID = ?", (student_id,)
            )
        if cursor.rowcount == 0:
            raise StudentNotFoundError(f"Student {student_id!r} was not found.")


class StudentRequestHandler(BaseHTTPRequestHandler):
    server: StudentApiServer

    def _send_json(self, status: HTTPStatus, body: object) -> None:
        encoded = json.dumps(body, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _read_json(self) -> dict[str, object]:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise InvalidStudentError("Content-Length must be an integer.") from error
        if content_length <= 0:
            raise InvalidStudentError("A JSON request body is required.")
        if content_length > 1_000_000:
            raise OverflowError("Request body exceeds the 1 MB limit.")
        if self.headers.get_content_type() != "application/json":
            raise InvalidStudentError("Content-Type must be application/json.")
        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise InvalidStudentError("Request body must contain valid JSON.") from error
        if not isinstance(payload, dict):
            raise InvalidStudentError("A student record must be a JSON object.")
        return payload

    def _student_id(self) -> str | None:
        parts = urlsplit(self.path).path.strip("/").split("/")
        if len(parts) == 2 and parts[0] == "students":
            return unquote(parts[1])
        return None

    def _handle_request(self, method: str) -> None:
        path = urlsplit(self.path).path.rstrip("/") or "/"
        if method == "GET" and path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
            return
        if method == "GET" and path == "/students":
            self._send_json(HTTPStatus.OK, self.server.store.list_students())
            return
        if method == "POST" and path == "/students":
            student = self.server.store.create_student(self._read_json())
            self._send_json(HTTPStatus.CREATED, student)
            return

        student_id = self._student_id()
        if student_id is None:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Route not found."})
            return
        if method == "GET":
            self._send_json(
                HTTPStatus.OK, self.server.store.get_student(student_id)
            )
        elif method == "PUT":
            student = self.server.store.update_student(
                student_id, self._read_json()
            )
            self._send_json(HTTPStatus.OK, student)
        elif method == "DELETE":
            self.server.store.delete_student(student_id)
            self._send_json(HTTPStatus.OK, {"deleted": student_id})

    def _dispatch(self, method: str) -> None:
        try:
            self._handle_request(method)
        except InvalidStudentError as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except OverflowError as error:
            self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": str(error)})
        except StudentNotFoundError as error:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": str(error)})
        except StudentAlreadyExistsError as error:
            self._send_json(HTTPStatus.CONFLICT, {"error": str(error)})

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def do_PUT(self) -> None:
        self._dispatch("PUT")

    def do_DELETE(self) -> None:
        self._dispatch("DELETE")


class StudentApiServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        address: tuple[str, int],
        store: StudentStore,
    ) -> None:
        super().__init__(address, partial(StudentRequestHandler))
        self.store = store


def main() -> None:
    database_path = Path(
        os.environ.get("STUDENT_DATABASE_PATH", str(DEFAULT_DATABASE_PATH))
    )
    store = StudentStore(database_path)
    host = os.environ.get("STUDENT_API_HOST", "127.0.0.1")
    port = int(os.environ.get("STUDENT_API_PORT", "8000"))
    with StudentApiServer((host, port), store) as server:
        print(f"Student API listening on http://{host}:{port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
