from bson import ObjectId
from pymongo.database import Database

from app.repositories.base import BaseRepository


class ReservaRepository(BaseRepository):
    def __init__(self, db: Database):
        super().__init__(db.reservas)

    def _confirmadas(self, clase_id: ObjectId, excluir_id: ObjectId | None) -> dict:
        filtro: dict = {"claseId": clase_id, "estado": "CONFIRMADA", "activo": True}
        if excluir_id is not None:
            filtro["_id"] = {"$ne": excluir_id}
        return filtro

    def count_confirmadas(self, clase_id: ObjectId, excluir_id: ObjectId | None = None) -> int:
        return self.col.count_documents(self._confirmadas(clase_id, excluir_id))

    def find_confirmada(self, socio_id: ObjectId, clase_id: ObjectId, excluir_id: ObjectId | None = None) -> dict | None:
        filtro = self._confirmadas(clase_id, excluir_id)
        filtro["socioId"] = socio_id
        return self.col.find_one(filtro)
