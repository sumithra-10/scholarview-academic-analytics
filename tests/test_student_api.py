from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from src.student_api import StudentApiServer, StudentStore
from src.student_api_client import (
    StudentApiError,
    create_student,
    delete_student,
    get_student,
    list_students,
    update_student,
)


def sample_student(student_id: str = "S901") -> dict[str, object]:
    return {
        "Student_ID": student_id,
        "Attendance_Percent": 82.5,
        "Study_Hours_Per_Week": 12,
        "Subject_Math": 70,
        "Subject_Python": 85,
        "Subject_DBMS": 76,
        "Subject_AI": 90,
        "Assignment_Score": 88,
        "Internal_Marks": 79,
        "Participation_Score": 92,
        "Previous_Semester_Score": 74,
    }


class StudentApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_directory.name) / "students.sqlite3"
        self.server = StudentApiServer(("127.0.0.1", 0), StudentStore(database_path, None))
        self.server_thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self.server_thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join(timeout=2)
        self.temp_directory.cleanup()

    def test_api_supports_student_crud(self) -> None:
        created = create_student(self.base_url, sample_student())
        self.assertEqual(created["Student_ID"], "S901")
        self.assertEqual(get_student(self.base_url, "S901")["Subject_AI"], 90)
        self.assertEqual(len(list_students(self.base_url)), 1)

        updated_record = sample_student()
        updated_record["Subject_AI"] = 95
        updated = update_student(self.base_url, "S901", updated_record)
        self.assertEqual(updated["Subject_AI"], 95)

        delete_student(self.base_url, "S901")
        self.assertEqual(list_students(self.base_url), [])

    def test_duplicate_student_returns_conflict(self) -> None:
        create_student(self.base_url, sample_student())
        with self.assertRaisesRegex(StudentApiError, "HTTP 409"):
            create_student(self.base_url, sample_student())

    def test_invalid_student_returns_bad_request(self) -> None:
        student = sample_student()
        student["Subject_Math"] = 120
        request = Request(
            f"{self.base_url}/students",
            data=json.dumps(student).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(HTTPError) as error:
            urlopen(request, timeout=2)
        self.assertEqual(error.exception.code, 400)
        error.exception.close()

    def test_missing_student_returns_not_found(self) -> None:
        with self.assertRaisesRegex(StudentApiError, "HTTP 404"):
            get_student(self.base_url, "unknown")

    def test_api_seeds_database_from_sample_csv(self) -> None:
        database_path = Path(self.temp_directory.name) / "seeded.sqlite3"
        seed_path = Path(__file__).resolve().parents[1] / "data" / "cleaned_student_data.csv"
        store = StudentStore(database_path, seed_path)
        self.assertEqual(len(store.list_students()), 100)

    def test_dashboard_reads_student_records_from_api(self) -> None:
        create_student(self.base_url, sample_student())
        from app import load_student_data

        frame = load_student_data(api_base_url=self.base_url)
        self.assertEqual(frame.loc[0, "Student_ID"], "S901")
        self.assertEqual(frame.loc[0, "Overall_Average"], 80.25)


if __name__ == "__main__":
    unittest.main()
