from bson import ObjectId
from pymongo.database import Database

from app.repositories.base import BaseRepository


class SocioRepository(BaseRepository):
    def __init__(self, db: Database):
        super().__init__(db.socios)

    def find_active_by_dni(self, dni: str, excluir_id: ObjectId | None = None) -> dict | None:
        filtro: dict = {"dni": dni, "activo": True}
        if excluir_id is not None:
            filtro["_id"] = {"$ne": excluir_id}
        return self.col.find_one(filtro)
