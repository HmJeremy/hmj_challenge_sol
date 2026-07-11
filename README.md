# Globant Data Engineer Challenge - Solucion

Migra datos historicos de contratacion a una base de datos SQL, expone una
API REST validada para ingesta batch, soporta backup/restore en AVRO, y
responde las preguntas de analitica de contrataciones 2021 via SQL.

## Stack

- **Base de datos**: SQLite via SQLAlchemy. `DATABASE_URL` en
  `app/database.py` es lo unico que habria que cambiar para apuntar esto a
  Postgres/MySQL.
- **API**: FastAPI (docs auto-generadas en `/docs`).
- **Formato de backup**: Apache Avro via `fastavro`.

## Estructura del proyecto

```
app/
  database.py     Engine/sesion de SQLAlchemy
  models.py       Modelos ORM: Department, Job, HiredEmployee
  schemas.py      Schemas de request de Pydantic (validacion estructural, batch 1-1000)
  validation.py   Validacion de negocio compartida (campos obligatorios, datetime ISO, FK)
  logger.py       Escribe cada registro rechazado en logs/invalid_records.log como JSON
  migration.py    Script de migracion de CSV historico -> DB
  backup.py       Backup/restore en AVRO por tabla
  analytics.py    SQL para las dos preguntas de analitica de contrataciones
  main.py         App de FastAPI que conecta todos los endpoints
data/             CSV de origen (departments, jobs, hired_employees)
tests/            suite de pytest (reglas de validacion + comportamiento de la API)
```

## Instalacion

Requiere Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 1. Migracion de datos historicos

Carga `data/departments.csv`, `data/jobs.csv`, `data/hired_employees.csv`
a la base de datos, validando cada fila de hired_employees y
saltando/logueando las invalidas (nunca se insertan).

```bash
python -m app.migration
```

La salida se ve asi:

```
departments loaded: 12
jobs loaded: 181
hired_employees: 1929 valid / 70 invalid (see logs/invalid_records.log)
```

## 2. Levantar la API

```bash
uvicorn app.main:app --reload
```

Docs: http://127.0.0.1:8000/docs

### Endpoints de ingesta (batch de 1-1000 filas)

Un endpoint por tabla, porque `hired_employees` necesita validacion de FK
contra `departments`/`jobs` que las otras dos no necesitan.

```bash
curl -X POST http://127.0.0.1:8000/departments \
  -H "Content-Type: application/json" \
  -d '{"records": [{"id": 13, "department": "Data Engineering"}]}'

curl -X POST http://127.0.0.1:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"records": [{"id": 200, "job": "Data Engineer"}]}'

curl -X POST http://127.0.0.1:8000/hired_employees \
  -H "Content-Type: application/json" \
  -d '{"records": [{"id": 5000, "name": "Ada Lovelace", "datetime": "2021-06-15T10:00:00Z", "department_id": 5, "job_id": 9}]}'
```

Cada respuesta reporta `inserted`, `rejected`, y los `errors` (registro +
motivo) de las filas rechazadas - nunca se escribe nada invalido en la DB.

### Reglas de validacion (hired_employees)

- `id`, `name`, `datetime`, `department_id`, `job_id` son todos obligatorios
- `datetime` debe ser ISO-8601 (ej. `2021-07-27T16:02:08Z`)
- `department_id` debe existir en `departments`
- `job_id` debe existir en `jobs`
- los `id` duplicados se rechazan

Los registros rechazados nunca se insertan y quedan como lineas JSON en
`logs/invalid_records.log`.

### Backup / Restore

```bash
curl -X POST http://127.0.0.1:8000/backup/hired_employees
# -> escribe backups/hired_employees.avro

curl -X POST http://127.0.0.1:8000/restore/hired_employees
# -> borra la tabla y la recarga desde backups/hired_employees.avro
```

### Analitica

Las dos consultas solo miran el 2021 y solo ven datos validos, ya que las
filas invalidas nunca se insertaron.

```bash
curl http://127.0.0.1:8000/analytics/hires-by-quarter
curl http://127.0.0.1:8000/analytics/departments-above-average
```

`hires-by-quarter` devuelve `department | job | Q1 | Q2 | Q3 | Q4`,
ordenado alfabeticamente por department y despues job.

`departments-above-average` devuelve `id | department | hired` para los
departamentos que contrataron mas gente en 2021 que el promedio de
**todos** los departamentos (incluyendo los que tuvieron cero
contrataciones en 2021, para que el promedio no quede inflado), ordenado
por `hired` DESC.

## Tests

```bash
pytest -v
```

Cubre las reglas de validacion directamente y el comportamiento end-to-end
de la API: ingesta/rechazo/limite de batch/backup-restore/analitica.

## Docker

```bash
docker build -t globant-challenge .
docker run -p 8000:8000 globant-challenge
```

Nota: el script de migracion no corre automatico dentro del contenedor;
hay que correrlo una vez via `docker exec <container> python -m app.migration`,
o agregarlo como override de `CMD` para un contenedor de migracion unico.
