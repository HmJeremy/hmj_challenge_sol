"""Reglas de validacion compartidas para los registros de hired_employees.

Las usan tanto el script de migracion historica como la API de ingesta, asi
los dos caminos nunca pueden estar en desacuerdo sobre que es un registro
valido: id, name, datetime, department_id y job_id son todos obligatorios;
datetime debe ser ISO-8601; department_id/job_id deben existir en sus
tablas respectivas.
"""
from datetime import datetime as dt
from typing import Any, Tuple

from sqlalchemy.orm import Session

from . import models

REQUIRED_FIELDS = ["id", "name", "datetime", "department_id", "job_id"]


def is_valid_iso_datetime(value: Any) -> bool:
    if value is None:
        return False
    try:
        # datetime.fromisoformat necesita "+00:00" en vez de una "Z" pelada
        dt.fromisoformat(str(value).replace("Z", "+00:00"))
        return True
    except (ValueError, TypeError):
        return False


def _to_int(value: Any):
    try:
        return int(value), None
    except (ValueError, TypeError):
        return None, f"value is not a valid integer: {value!r}"


def validate_hired_employee(record: dict, db: Session) -> Tuple[bool, str]:
    """Valida un registro individual de hired_employees.

    `record` puede venir de una fila de CSV cruda (strings) o de un body
    JSON ya parseado (ints) - los dos casos se manejan igual.
    """
    for field in REQUIRED_FIELDS:
        value = record.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return False, f"missing required field: {field}"

    _, id_err = _to_int(record["id"])
    if id_err:
        return False, f"id {id_err}"

    if not is_valid_iso_datetime(record["datetime"]):
        return False, f"invalid datetime format (expected ISO-8601): {record['datetime']!r}"

    department_id, dept_err = _to_int(record["department_id"])
    if dept_err:
        return False, f"department_id {dept_err}"

    job_id, job_err = _to_int(record["job_id"])
    if job_err:
        return False, f"job_id {job_err}"

    if not db.query(models.Department.id).filter_by(id=department_id).first():
        return False, f"department_id {department_id} does not exist"

    if not db.query(models.Job.id).filter_by(id=job_id).first():
        return False, f"job_id {job_id} does not exist"

    return True, ""
