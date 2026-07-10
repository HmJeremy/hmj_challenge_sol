"""Backup (exporta a AVRO) y restore (carga desde AVRO) para cada tabla."""
import os

import fastavro
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from . import models

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.environ.get("GLOBANT_BACKUP_DIR", os.path.join(BASE_DIR, "backups"))
os.makedirs(BACKUP_DIR, exist_ok=True)

TABLE_MODELS = {
    "departments": models.Department,
    "jobs": models.Job,
    "hired_employees": models.HiredEmployee,
}

AVRO_SCHEMAS = {
    "departments": {
        "type": "record",
        "name": "Department",
        "fields": [
            {"name": "id", "type": "int"},
            {"name": "department", "type": "string"},
        ],
    },
    "jobs": {
        "type": "record",
        "name": "Job",
        "fields": [
            {"name": "id", "type": "int"},
            {"name": "job", "type": "string"},
        ],
    },
    "hired_employees": {
        "type": "record",
        "name": "HiredEmployee",
        "fields": [
            {"name": "id", "type": "int"},
            {"name": "name", "type": "string"},
            {"name": "datetime", "type": "string"},
            {"name": "department_id", "type": "int"},
            {"name": "job_id", "type": "int"},
        ],
    },
}


def _backup_path(table: str) -> str:
    return os.path.join(BACKUP_DIR, f"{table}.avro")


def backup_table(table: str, db: Session) -> str:
    if table not in TABLE_MODELS:
        raise ValueError(f"unknown table: {table}")

    model = TABLE_MODELS[table]
    columns = [c.key for c in inspect(model).mapper.column_attrs]
    rows = db.query(model).all()
    records = [{col: getattr(row, col) for col in columns} for row in rows]

    path = _backup_path(table)
    with open(path, "wb") as out:
        fastavro.writer(out, AVRO_SCHEMAS[table], records)
    return path


def restore_table(table: str, db: Session, file_path: str | None = None) -> int:
    if table not in TABLE_MODELS:
        raise ValueError(f"unknown table: {table}")

    model = TABLE_MODELS[table]
    path = file_path or _backup_path(table)
    if not os.path.exists(path):
        raise FileNotFoundError(f"backup file not found: {path}")

    with open(path, "rb") as f:
        records = list(fastavro.reader(f))

    db.query(model).delete()
    if records:
        db.bulk_insert_mappings(model, records)
    db.commit()
    return len(records)
