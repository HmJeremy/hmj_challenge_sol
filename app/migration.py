"""Migracion de datos historicos: carga los 3 CSV a la base de datos SQL.

Correr con: python -m app.migration

departments.csv y jobs.csv se cargan primero porque las filas de
hired_employees se validan contra ellas. hired_employees.csv se inserta
en lotes de BATCH_SIZE; las filas invalidas se saltan y quedan logueadas,
nunca se insertan.
"""
import csv
import os

from .database import Base, SessionLocal, engine
from .logger import log_invalid
from . import models
from .validation import validate_hired_employee

DATA_DIR = os.environ.get(
    "GLOBANT_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"),
)
BATCH_SIZE = 1000


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def load_departments(db) -> int:
    path = os.path.join(DATA_DIR, "departments.csv")
    count = 0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 2 or not row[0].strip() or not row[1].strip():
                log_invalid("departments", row, "missing id or department name")
                continue
            try:
                dept_id = int(row[0])
            except ValueError:
                log_invalid("departments", row, "id is not a valid integer")
                continue
            db.merge(models.Department(id=dept_id, department=row[1]))
            count += 1
    db.commit()
    return count


def load_jobs(db) -> int:
    path = os.path.join(DATA_DIR, "jobs.csv")
    count = 0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 2 or not row[0].strip() or not row[1].strip():
                log_invalid("jobs", row, "missing id or job name")
                continue
            try:
                job_id = int(row[0])
            except ValueError:
                log_invalid("jobs", row, "id is not a valid integer")
                continue
            db.merge(models.Job(id=job_id, job=row[1]))
            count += 1
    db.commit()
    return count


def load_hired_employees(db) -> tuple[int, int]:
    path = os.path.join(DATA_DIR, "hired_employees.csv")
    valid_count = 0
    invalid_count = 0
    batch: list[dict] = []

    def flush(rows):
        if rows:
            db.bulk_insert_mappings(models.HiredEmployee, rows)
            db.commit()

    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            record = {
                "id": row[0] if len(row) > 0 else None,
                "name": row[1] if len(row) > 1 else None,
                "datetime": row[2] if len(row) > 2 else None,
                "department_id": row[3] if len(row) > 3 else None,
                "job_id": row[4] if len(row) > 4 else None,
            }

            ok, reason = validate_hired_employee(record, db)
            if not ok:
                log_invalid("hired_employees", row, reason)
                invalid_count += 1
                continue

            batch.append(
                {
                    "id": int(record["id"]),
                    "name": record["name"],
                    "datetime": record["datetime"],
                    "department_id": int(record["department_id"]),
                    "job_id": int(record["job_id"]),
                }
            )
            valid_count += 1

            if len(batch) >= BATCH_SIZE:
                flush(batch)
                batch = []

        flush(batch)

    return valid_count, invalid_count


def run() -> None:
    init_db()
    db = SessionLocal()
    try:
        n_dept = load_departments(db)
        n_jobs = load_jobs(db)
        valid, invalid = load_hired_employees(db)
        print(f"departments loaded: {n_dept}")
        print(f"jobs loaded: {n_jobs}")
        print(f"hired_employees: {valid} valid / {invalid} invalid (see logs/invalid_records.log)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
