"""Funciones auxiliares compartidas por las capas."""
from datetime import datetime, timezone

from bson import Decimal128, ObjectId
from bson.errors import InvalidId

from app.exceptions import BadRequestError


def utcnow() -> datetime:
    """Ahora en UTC, truncado a milisegundos (la precisión de MongoDB) para que lo que se
    responde al crear coincida exactamente con lo que queda guardado."""
    ahora = datetime.now(timezone.utc)
    return ahora.replace(microsecond=ahora.microsecond // 1000 * 1000)


def to_object_id(valor: str, campo: str = "id") -> ObjectId:
    try:
        return ObjectId(valor)
    except (InvalidId, TypeError):
        raise BadRequestError(f"'{valor}' no es un {campo} válido (deben ser 24 caracteres hexadecimales)")


def serialize(valor):
    """Convierte un documento de Mongo a algo serializable: _id -> id, ObjectId -> str,
    Decimal128 -> float, fechas con UTC."""
    if isinstance(valor, ObjectId):
        return str(valor)
    if isinstance(valor, Decimal128):
        return float(valor.to_decimal())
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=timezone.utc) if valor.tzinfo is None else valor
    if isinstance(valor, dict):
        return {("id" if k == "_id" else k): serialize(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [serialize(v) for v in valor]
    return valor


def flatten_update(datos: dict, anidados: tuple[str, ...] = ("membresia", "instructor")) -> dict:
    """Pasa {'membresia': {'plan': 'X'}} a {'membresia.plan': 'X'} para modificar solo ese subcampo."""
    plano: dict = {}
    for clave, valor in datos.items():
        if clave in anidados and isinstance(valor, dict):
            for sub, v in valor.items():
                plano[f"{clave}.{sub}"] = v
        else:
            plano[clave] = valor
    return plano
