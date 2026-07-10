"""Schemas de Pydantic para la API de ingesta.

Estos validan lo estructural (tipos, campos obligatorios, tamano de batch
1-1000). La validacion referencial (department_id/job_id deben existir)
necesita sesion de DB y vive en validation.py, encima de estos schemas.
"""
from typing import List

from pydantic import BaseModel, Field


class DepartmentIn(BaseModel):
    id: int
    department: str = Field(..., min_length=1)


class JobIn(BaseModel):
    id: int
    job: str = Field(..., min_length=1)


class HiredEmployeeIn(BaseModel):
    id: int
    name: str = Field(..., min_length=1)
    datetime: str = Field(..., min_length=1)
    department_id: int
    job_id: int


class DepartmentBatch(BaseModel):
    records: List[DepartmentIn] = Field(..., min_length=1, max_length=1000)


class JobBatch(BaseModel):
    records: List[JobIn] = Field(..., min_length=1, max_length=1000)


class HiredEmployeeBatch(BaseModel):
    records: List[HiredEmployeeIn] = Field(..., min_length=1, max_length=1000)
