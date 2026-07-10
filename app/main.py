"""App de FastAPI: endpoints de ingesta, backup/restore y analitica."""
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import backup, models, schemas
from .database import Base, engine, get_db
from .logger import log_invalid
from .validation import validate_hired_employee

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Globant Data Engineer Challenge API",
    description=(
        "API para migracion de datos historicos, ingesta batch con "
        "validacion, backup/restore en AVRO, y analitica de contrataciones 2021."
    ),
    version="1.0.0",
)


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}


# --------------------------------------------------------------------------
# Ingesta - batch de 1 a 1000 filas por request
# --------------------------------------------------------------------------


@app.post("/departments", status_code=201)
def ingest_departments(batch: schemas.DepartmentBatch, db: Session = Depends(get_db)):
    inserted, errors = 0, []
    for rec in batch.records:
        if db.query(models.Department.id).filter_by(id=rec.id).first():
            reason = "id already exists"
            errors.append({"record": rec.model_dump(), "reason": reason})
            log_invalid("departments", rec.model_dump(), reason)
            continue
        db.add(models.Department(id=rec.id, department=rec.department))
        inserted += 1
    db.commit()
    return {"inserted": inserted, "rejected": len(errors), "errors": errors}


@app.post("/jobs", status_code=201)
def ingest_jobs(batch: schemas.JobBatch, db: Session = Depends(get_db)):
    inserted, errors = 0, []
    for rec in batch.records:
        if db.query(models.Job.id).filter_by(id=rec.id).first():
            reason = "id already exists"
            errors.append({"record": rec.model_dump(), "reason": reason})
            log_invalid("jobs", rec.model_dump(), reason)
            continue
        db.add(models.Job(id=rec.id, job=rec.job))
        inserted += 1
    db.commit()
    return {"inserted": inserted, "rejected": len(errors), "errors": errors}


@app.post("/hired_employees", status_code=201)
def ingest_hired_employees(batch: schemas.HiredEmployeeBatch, db: Session = Depends(get_db)):
    inserted, errors = 0, []
    for rec in batch.records:
        record = rec.model_dump()
        ok, reason = validate_hired_employee(record, db)
        if not ok:
            errors.append({"record": record, "reason": reason})
            log_invalid("hired_employees", record, reason)
            continue
        if db.query(models.HiredEmployee.id).filter_by(id=record["id"]).first():
            reason = "id already exists"
            errors.append({"record": record, "reason": reason})
            log_invalid("hired_employees", record, reason)
            continue
        db.add(models.HiredEmployee(**record))
        inserted += 1
    db.commit()
    return {"inserted": inserted, "rejected": len(errors), "errors": errors}


# --------------------------------------------------------------------------
# Backup / Restore
# --------------------------------------------------------------------------


@app.post("/backup/{table}")
def create_backup(table: str, db: Session = Depends(get_db)):
    try:
        path = backup.backup_table(table, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"table": table, "backup_file": path}


@app.post("/restore/{table}")
def restore_backup(table: str, db: Session = Depends(get_db)):
    try:
        count = backup.restore_table(table, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"table": table, "restored_records": count}
