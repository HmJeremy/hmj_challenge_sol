"""Modelos ORM de SQLAlchemy: Department, Job, HiredEmployee."""
from sqlalchemy import Column, ForeignKey, Integer, String

from .database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=False)
    department = Column(String, nullable=False)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=False)
    job = Column(String, nullable=False)


class HiredEmployee(Base):
    __tablename__ = "hired_employees"

    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String, nullable=False)
    datetime = Column(String, nullable=False)  # se guarda como texto ISO-8601
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
