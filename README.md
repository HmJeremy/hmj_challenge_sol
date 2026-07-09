# Globant Data Engineer Challenge - Solucion

Migra datos historicos de contratacion a una base de datos SQL, expone una
API REST validada para ingesta batch, soporta backup/restore en AVRO, y
responde las preguntas de analitica de contrataciones 2021 via SQL.

## Stack

- **Base de datos**: SQLite via SQLAlchemy. Facil de apuntar a Postgres/MySQL
  despues cambiando `DATABASE_URL`.
- **API**: FastAPI (docs auto-generadas en `/docs`).
- **Formato de backup**: Apache Avro via `fastavro`.

## Instalacion

Requiere Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

WIP: voy a ir documentando cada parte (migracion, API, backup, analitica) a
medida que la implemento.
