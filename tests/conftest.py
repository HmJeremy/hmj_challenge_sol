import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()


def _mssql_url() -> str:
    driver = os.environ.get("DB_ODBC_DRIVER", "ODBC Driver 17 for SQL Server").replace(" ", "+")
    encrypt = "yes" if os.environ.get("DB_ENCRYPT", "false").lower() == "true" else "no"
    trust_cert = "yes" if os.environ.get("DB_TRUST_SERVER_CERTIFICATE", "false").lower() == "true" else "no"
    return (
        f"mssql+pyodbc://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_SERVER']},{os.environ.get('DB_PORT', '1433')}/{os.environ['DB_DATABASE']}"
        f"?driver={driver}&Encrypt={encrypt}&TrustServerCertificate={trust_cert}"
    )


test_engine = create_engine(_mssql_url())
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _clear_tables(session, models) -> None:
    # orden por FK: hired_employees primero, despues departments/jobs
    session.query(models.HiredEmployee).delete()
    session.query(models.Department).delete()
    session.query(models.Job).delete()
    session.commit()


@pytest.fixture()
def db_session(monkeypatch):
    """Sesion contra el SQL Server real de test (test_hmj).

    Las tablas se limpian antes y despues de cada test para que las
    corridas sean repetibles y no choquen por id duplicado.
    """
    from app import database, models

    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "SessionLocal", TestSessionLocal)

    models.Base.metadata.create_all(bind=test_engine)

    session = TestSessionLocal()
    _clear_tables(session, models)
    try:
        yield session
    finally:
        session.rollback()
        _clear_tables(session, models)
        session.close()


@pytest.fixture()
def client(db_session, monkeypatch):
    from app import database, main

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    main.app.dependency_overrides[database.get_db] = override_get_db
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()
