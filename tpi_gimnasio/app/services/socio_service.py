"""Reglas de negocio de socios. No conoce HTTP ni el driver: habla con el repositorio."""
from pymongo.errors import DuplicateKeyError

from app.exceptions import BadRequestError, ConflictError, NotFoundError
from app.repositories.socio_repository import SocioRepository
from app.schemas.socio import SocioCreate, SocioUpdate
from app.utils import flatten_update, to_object_id, utcnow


class SocioService:
    def __init__(self, repo: SocioRepository):
        self.repo = repo

    def crear(self, datos: SocioCreate) -> dict:
        doc = datos.model_dump(exclude_none=True)  # no se guardan campos null: el validador exige string
        self._validar_dni_libre(doc["dni"])
        doc.update(fechaAlta=utcnow(), activo=True, fechaBaja=None)
        try:
            return self.repo.insert(doc)
        except DuplicateKeyError:
            raise ConflictError(f"Ya existe un socio activo con DNI {doc['dni']}")

    def listar(self, skip: int, limit: int) -> list[dict]:
        return self.repo.find_active(skip=skip, limit=limit)

    def obtener(self, socio_id: str) -> dict:
        socio = self.repo.find_active_by_id(to_object_id(socio_id, "id de socio"))
        if socio is None:
            raise NotFoundError("Socio no encontrado")
        return socio

    def actualizar(self, socio_id: str, datos: SocioUpdate) -> dict:
        oid = to_object_id(socio_id, "id de socio")
        cambios = flatten_update(datos.model_dump(exclude_none=True))
        if not cambios:
            raise BadRequestError("No se enviaron campos para actualizar")
        if "dni" in cambios:
            self._validar_dni_libre(cambios["dni"], excluir_id=oid)
        try:
            socio = self.repo.update_active(oid, cambios)
        except DuplicateKeyError:
            raise ConflictError(f"Ya existe un socio activo con DNI {cambios['dni']}")
        if socio is None:
            raise NotFoundError("Socio no encontrado")
        return socio

    def eliminar(self, socio_id: str) -> dict:
        """Baja lógica: activo=False y fechaBaja=ahora. El documento no se borra."""
        socio = self.repo.soft_delete(to_object_id(socio_id, "id de socio"))
        if socio is None:
            raise NotFoundError("Socio no encontrado")
        return socio

    def _validar_dni_libre(self, dni: str, excluir_id=None) -> None:
        if self.repo.find_active_by_dni(dni, excluir_id) is not None:
            raise ConflictError(f"Ya existe un socio activo con DNI {dni}")
