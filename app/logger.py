"""Logueo de registros invalidos.

Cada registro rechazado (de la migracion historica o de la API) se escribe
como una linea JSON en logs/invalid_records.log, para que nada se pierda
en silencio y el log se pueda grepear/parsear despues.
"""
import json
import logging
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.environ.get("GLOBANT_LOG_DIR", os.path.join(BASE_DIR, "logs"))
os.makedirs(LOG_DIR, exist_ok=True)

_logger = logging.getLogger("globant.invalid_records")
_logger.setLevel(logging.INFO)
if not _logger.handlers:
    handler = logging.FileHandler(os.path.join(LOG_DIR, "invalid_records.log"))
    handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(handler)
    _logger.propagate = False


def log_invalid(table: str, record, reason: str) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "table": table,
        "record": record,
        "reason": reason,
    }
    _logger.info(json.dumps(entry, default=str, ensure_ascii=False))
