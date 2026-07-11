"""Consultas SQL de analitica para los datos de contratacion 2021.

Las dos consultas solo consideran contrataciones del 2021 y solo ven
registros validos, ya que las filas invalidas nunca se insertaron durante
la ingesta.

Hay una version por dialecto porque `strftime` es especifico de SQLite;
en SQL Server el equivalente es convertir el texto ISO-8601 guardado en
`datetime` a `datetimeoffset` (entiende el sufijo "Z") y usar DATEPART.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

HIRES_BY_QUARTER_SQLITE = text(
    """
    SELECT
        d.department AS department,
        j.job AS job,
        SUM(CASE WHEN CAST(strftime('%m', he.datetime) AS INTEGER) BETWEEN 1 AND 3 THEN 1 ELSE 0 END) AS Q1,
        SUM(CASE WHEN CAST(strftime('%m', he.datetime) AS INTEGER) BETWEEN 4 AND 6 THEN 1 ELSE 0 END) AS Q2,
        SUM(CASE WHEN CAST(strftime('%m', he.datetime) AS INTEGER) BETWEEN 7 AND 9 THEN 1 ELSE 0 END) AS Q3,
        SUM(CASE WHEN CAST(strftime('%m', he.datetime) AS INTEGER) BETWEEN 10 AND 12 THEN 1 ELSE 0 END) AS Q4
    FROM hired_employees he
    JOIN departments d ON he.department_id = d.id
    JOIN jobs j ON he.job_id = j.id
    WHERE strftime('%Y', he.datetime) = '2021'
    GROUP BY d.department, j.job
    ORDER BY d.department ASC, j.job ASC
    """
)

# Los departamentos con cero contrataciones en 2021 entran por el LEFT JOIN
# para que el promedio se calcule sobre *todos* los departamentos, no solo
# los que contrataron a alguien.
DEPARTMENTS_ABOVE_AVERAGE_SQLITE = text(
    """
    WITH dept_counts AS (
        SELECT
            d.id AS id,
            d.department AS department,
            COUNT(he.id) AS hired
        FROM departments d
        LEFT JOIN hired_employees he
            ON he.department_id = d.id
           AND strftime('%Y', he.datetime) = '2021'
        GROUP BY d.id, d.department
    )
    SELECT id, department, hired
    FROM dept_counts
    WHERE hired > (SELECT AVG(hired) FROM dept_counts)
    ORDER BY hired DESC
    """
)

HIRES_BY_QUARTER_MSSQL = text(
    """
    SELECT
        d.department AS department,
        j.job AS job,
        SUM(CASE WHEN DATEPART(MONTH, TRY_CONVERT(datetimeoffset, he.datetime)) BETWEEN 1 AND 3 THEN 1 ELSE 0 END) AS Q1,
        SUM(CASE WHEN DATEPART(MONTH, TRY_CONVERT(datetimeoffset, he.datetime)) BETWEEN 4 AND 6 THEN 1 ELSE 0 END) AS Q2,
        SUM(CASE WHEN DATEPART(MONTH, TRY_CONVERT(datetimeoffset, he.datetime)) BETWEEN 7 AND 9 THEN 1 ELSE 0 END) AS Q3,
        SUM(CASE WHEN DATEPART(MONTH, TRY_CONVERT(datetimeoffset, he.datetime)) BETWEEN 10 AND 12 THEN 1 ELSE 0 END) AS Q4
    FROM hired_employees he
    JOIN departments d ON he.department_id = d.id
    JOIN jobs j ON he.job_id = j.id
    WHERE DATEPART(YEAR, TRY_CONVERT(datetimeoffset, he.datetime)) = 2021
    GROUP BY d.department, j.job
    ORDER BY d.department ASC, j.job ASC
    """
)

DEPARTMENTS_ABOVE_AVERAGE_MSSQL = text(
    """
    WITH dept_counts AS (
        SELECT
            d.id AS id,
            d.department AS department,
            COUNT(he.id) AS hired
        FROM departments d
        LEFT JOIN hired_employees he
            ON he.department_id = d.id
           AND DATEPART(YEAR, TRY_CONVERT(datetimeoffset, he.datetime)) = 2021
        GROUP BY d.id, d.department
    )
    SELECT id, department, hired
    FROM dept_counts
    WHERE hired > (SELECT AVG(hired * 1.0) FROM dept_counts)
    ORDER BY hired DESC
    """
)


def _pick(db: Session, sqlite_query, mssql_query):
    return mssql_query if db.get_bind().dialect.name == "mssql" else sqlite_query


def hires_by_quarter(db: Session) -> list[dict]:
    query = _pick(db, HIRES_BY_QUARTER_SQLITE, HIRES_BY_QUARTER_MSSQL)
    rows = db.execute(query).mappings().all()
    return [dict(r) for r in rows]


def departments_above_average(db: Session) -> list[dict]:
    query = _pick(db, DEPARTMENTS_ABOVE_AVERAGE_SQLITE, DEPARTMENTS_ABOVE_AVERAGE_MSSQL)
    rows = db.execute(query).mappings().all()
    return [dict(r) for r in rows]
