from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class _Entrada(BaseModel):
    """Base de los modelos de entrada: recorta espacios y rechaza campos desconocidos
    (así nadie puede mandar 'activo' o 'fechaBaja' desde afuera)."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class Membresia(_Entrada):
    plan: str = Field(..., min_length=1, max_length=40, examples=["MENSUAL"])
    precio: float | None = Field(None, ge=0, examples=[25000])
    fechaInicio: datetime | None = Field(None, examples=["2026-11-10T00:00:00Z"])
    fechaVencimiento: datetime | None = Field(None, examples=["2026-11-10T00:00:00Z"])


class MembresiaUpdate(_Entrada):
    plan: str | None = Field(None, min_length=1, max_length=40)
    precio: float | None = Field(None, ge=0)
    fechaInicio: datetime | None = None
    fechaVencimiento: datetime | None = None


class SocioCreate(_Entrada):
    dni: str = Field(..., min_length=6, max_length=12, pattern=r"^\d+$", examples=["30123456"])
    nombre: str = Field(..., min_length=1, max_length=80, examples=["Lucía"])
    apellido: str = Field(..., min_length=1, max_length=80, examples=["Fernández"])
    email: EmailStr = Field(..., examples=["lucia@example.com"])
    telefono: str | None = Field(None, max_length=30, examples=["3515551234"])
    membresia: Membresia


class SocioUpdate(_Entrada):
    dni: str | None = Field(None, min_length=6, max_length=12, pattern=r"^\d+$")
    nombre: str | None = Field(None, min_length=1, max_length=80)
    apellido: str | None = Field(None, min_length=1, max_length=80)
    email: EmailStr | None = None
    telefono: str | None = Field(None, max_length=30)
    membresia: MembresiaUpdate | None = None


class MembresiaOut(BaseModel):
    plan: str
    precio: float | None = None
    fechaInicio: datetime | None = None
    fechaVencimiento: datetime | None = None


class SocioOut(BaseModel):
    id: str
    dni: str
    nombre: str
    apellido: str
    email: str
    telefono: str | None = None
    fechaAlta: datetime | None = None
    membresia: MembresiaOut
    activo: bool
    fechaBaja: datetime | None = None
