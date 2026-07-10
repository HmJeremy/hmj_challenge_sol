from app import models
from app.validation import is_valid_iso_datetime, validate_hired_employee


def test_is_valid_iso_datetime_accepts_zulu_format():
    assert is_valid_iso_datetime("2021-07-27T16:02:08Z") is True


def test_is_valid_iso_datetime_rejects_garbage():
    assert is_valid_iso_datetime("not-a-date") is False
    assert is_valid_iso_datetime(None) is False
    assert is_valid_iso_datetime("") is False


def test_validate_hired_employee_rejects_missing_field(db_session):
    record = {"id": 1, "name": "", "datetime": "2021-01-01T00:00:00Z", "department_id": 1, "job_id": 1}
    ok, reason = validate_hired_employee(record, db_session)
    assert ok is False
    assert "name" in reason


def test_validate_hired_employee_rejects_bad_datetime(db_session):
    db_session.add(models.Department(id=1, department="Engineering"))
    db_session.add(models.Job(id=1, job="Recruiter"))
    db_session.commit()

    record = {"id": 1, "name": "Jane", "datetime": "27/07/2021", "department_id": 1, "job_id": 1}
    ok, reason = validate_hired_employee(record, db_session)
    assert ok is False
    assert "datetime" in reason


def test_validate_hired_employee_rejects_unknown_department(db_session):
    db_session.add(models.Job(id=1, job="Recruiter"))
    db_session.commit()

    record = {"id": 1, "name": "Jane", "datetime": "2021-01-01T00:00:00Z", "department_id": 999, "job_id": 1}
    ok, reason = validate_hired_employee(record, db_session)
    assert ok is False
    assert "department_id" in reason


def test_validate_hired_employee_accepts_valid_record(db_session):
    db_session.add(models.Department(id=1, department="Engineering"))
    db_session.add(models.Job(id=1, job="Recruiter"))
    db_session.commit()

    record = {"id": 1, "name": "Jane", "datetime": "2021-01-01T00:00:00Z", "department_id": 1, "job_id": 1}
    ok, reason = validate_hired_employee(record, db_session)
    assert ok is True
    assert reason == ""
