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


def _use_mssql() -> bool:
    return bool(os.environ.get("DB_SERVER"))


def _clear_tables(session, models) -> None:
    # orden por FK: hired_employees primero, despues departments/jobs
    session.query(models.HiredEmployee).delete()
    session.query(models.Department).delete()
    session.query(models.Job).delete()
    session.commit()


@pytest.fixture()
def db_session(monkeypatch, tmp_path):
    """DB de test.

    Por defecto usa un SQLite aislado por test (no requiere nada instalado
    ni configurado, asi corre en cualquier maquina). Si hay un .env con las
    credenciales de un SQL Server (DB_SERVER en el entorno), usa ese en su
    lugar y limpia las tablas antes/despues de cada test para que las
    corridas sean repetibles.
    """
    from app import database, models

    if _use_mssql():
        engine = create_engine(_mssql_url())
    else:
        db_file = tmp_path / "test.db"
        engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", SessionLocal)

    models.Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    if _use_mssql():
        _clear_tables(session, models)
    try:
        yield session
    finally:
        session.rollback()
        # KEEP_TEST_DATA=1 salta solo la limpieza de salida, para poder
        # inspeccionar en SQL Server lo que dejo el ultimo test corrido.
        if _use_mssql() and not os.environ.get("KEEP_TEST_DATA"):
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
