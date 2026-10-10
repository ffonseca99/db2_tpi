from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class _Entrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class Instructor(_Entrada):
    nombre: str = Field(..., min_length=1, max_length=80, examples=["Martín"])
    especialidad: str | None = Field(None, max_length=80, examples=["Boxeo"])


class InstructorUpdate(_Entrada):
    nombre: str | None = Field(None, min_length=1, max_length=80)
    especialidad: str | None = Field(None, max_length=80)


class ClaseCreate(_Entrada):
    """Una clase es UNA ocurrencia real: si hay boxeo hoy y mañana, son dos documentos."""
    nombre: str = Field(..., min_length=1, max_length=80, examples=["Boxeo"])
    instructor: Instructor
    cupoMaximo: int = Field(..., ge=1, le=500, examples=[20])
    sala: str | None = Field(None, max_length=40, examples=["Sala 1"])
    fechaInicio: datetime = Field(..., description="Momento en que inicia la clase. Conviene enviarlo en UTC (con 'Z').",
                                  examples=["2026-10-20T22:00:00Z"])


class ClaseUpdate(_Entrada):
    nombre: str | None = Field(None, min_length=1, max_length=80)
    instructor: InstructorUpdate | None = None
    cupoMaximo: int | None = Field(None, ge=1, le=500)
    sala: str | None = Field(None, max_length=40)
    fechaInicio: datetime | None = None


class InstructorOut(BaseModel):
    nombre: str
    especialidad: str | None = None


class ClaseOut(BaseModel):
    id: str
    nombre: str
    instructor: InstructorOut
    cupoMaximo: int
    sala: str | None = None
    fechaAlta: datetime | None = None
    fechaInicio: datetime | None = None
    activo: bool
    fechaBaja: datetime | None = None
