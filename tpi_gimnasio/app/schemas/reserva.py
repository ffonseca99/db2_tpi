from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Estado = Literal["CONFIRMADA", "CANCELADA"]
OBJECT_ID = r"^[0-9a-fA-F]{24}$"


class _Entrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class ReservaCreate(_Entrada):
    socioId: str = Field(..., pattern=OBJECT_ID, examples=["670000000000000000000001"])
    claseId: str = Field(..., pattern=OBJECT_ID, examples=["670000000000000000000002"])


class ReservaUpdate(_Entrada):
    estado: Estado | None = None


class ReservaOut(BaseModel):
    id: str
    socioId: str
    claseId: str
    estado: Estado
    activo: bool
    fechaBaja: datetime | None = None
