"""Repositorio base: único lugar que habla con MongoDB y donde vive la baja lógica."""
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.collection import Collection

from app.utils import utcnow


class BaseRepository:
    def __init__(self, coleccion: Collection):
        self.col = coleccion

    # CREATE
    def insert(self, doc: dict) -> dict:
        self.col.insert_one(doc)  # pymongo agrega el _id al mismo diccionario
        return doc

    # READ: siempre filtra activo=True, nunca devuelve registros dados de baja
    def find_active(self, filtro: dict | None = None, skip: int = 0, limit: int = 50) -> list[dict]:
        consulta = {**(filtro or {}), "activo": True}
        return list(self.col.find(consulta).sort("_id", 1).skip(skip).limit(limit))

    def find_active_by_id(self, oid: ObjectId) -> dict | None:
        return self.col.find_one({"_id": oid, "activo": True})

    # UPDATE: solo sobre registros activos; devuelve el documento actualizado o None
    def update_active(self, oid: ObjectId, cambios: dict) -> dict | None:
        return self.col.find_one_and_update(
            {"_id": oid, "activo": True},
            {"$set": cambios},
            return_document=ReturnDocument.AFTER,
        )

    # DELETE (baja lógica): el documento queda en la base con activo=False
    def soft_delete(self, oid: ObjectId) -> dict | None:
        return self.col.find_one_and_update(
            {"_id": oid, "activo": True},
            {"$set": {"activo": False, "fechaBaja": utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
