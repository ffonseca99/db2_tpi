"""Reglas de negocio de clases."""
from app.exceptions import BadRequestError, NotFoundError
from app.repositories.clase_repository import ClaseRepository
from app.schemas.clase import ClaseCreate, ClaseUpdate
from app.utils import flatten_update, to_object_id, utcnow


class ClaseService:
    def __init__(self, repo: ClaseRepository):
        self.repo = repo

    def crear(self, datos: ClaseCreate) -> dict:
        doc = datos.model_dump(exclude_none=True)
        doc.update(fechaAlta=utcnow(), activo=True, fechaBaja=None)
        return self.repo.insert(doc)

    def listar(self, skip: int, limit: int) -> list[dict]:
        return self.repo.find_active(skip=skip, limit=limit)

    def obtener(self, clase_id: str) -> dict:
        clase = self.repo.find_active_by_id(to_object_id(clase_id, "id de clase"))
        if clase is None:
            raise NotFoundError("Clase no encontrada")
        return clase

    def actualizar(self, clase_id: str, datos: ClaseUpdate) -> dict:
        oid = to_object_id(clase_id, "id de clase")
        cambios = flatten_update(datos.model_dump(exclude_none=True))
        if not cambios:
            raise BadRequestError("No se enviaron campos para actualizar")
        clase = self.repo.update_active(oid, cambios)
        if clase is None:
            raise NotFoundError("Clase no encontrada")
        return clase

    def eliminar(self, clase_id: str) -> dict:
        """Baja lógica: activo=False y fechaBaja=ahora."""
        clase = self.repo.soft_delete(to_object_id(clase_id, "id de clase"))
        if clase is None:
            raise NotFoundError("Clase no encontrada")
        return clase
