"""Consultas SQL de analitica para los datos de contratacion 2021.

Las dos consultas solo consideran contrataciones del 2021 y solo ven
registros validos, ya que las filas invalidas nunca se insertaron durante
la ingesta.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

HIRES_BY_QUARTER_QUERY = text(
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
DEPARTMENTS_ABOVE_AVERAGE_QUERY = text(
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


def hires_by_quarter(db: Session) -> list[dict]:
    rows = db.execute(HIRES_BY_QUARTER_QUERY).mappings().all()
    return [dict(r) for r in rows]


def departments_above_average(db: Session) -> list[dict]:
    rows = db.execute(DEPARTMENTS_ABOVE_AVERAGE_QUERY).mappings().all()
    return [dict(r) for r in rows]
