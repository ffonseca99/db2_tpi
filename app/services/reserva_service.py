"""Reglas de negocio de reservas: socio y clase deben estar activos, sin duplicados y con cupo."""
from bson import ObjectId

from app.exceptions import BadRequestError, BusinessRuleError, ConflictError, NotFoundError
from app.repositories.clase_repository import ClaseRepository
from app.repositories.reserva_repository import ReservaRepository
from app.repositories.socio_repository import SocioRepository
from app.schemas.reserva import ReservaCreate, ReservaUpdate
from app.utils import to_object_id


class ReservaService:
    def __init__(self, repo: ReservaRepository, socios: SocioRepository, clases: ClaseRepository):
        self.repo = repo
        self.socios = socios
        self.clases = clases

    def crear(self, datos: ReservaCreate) -> dict:
        socio_id = to_object_id(datos.socioId, "socioId")
        clase_id = to_object_id(datos.claseId, "claseId")

        if self.socios.find_active_by_id(socio_id) is None:
            raise BusinessRuleError("El socio indicado no existe o está dado de baja")
        clase = self.clases.find_active_by_id(clase_id)
        if clase is None:
            raise BusinessRuleError("La clase indicada no existe o está dada de baja")

        self._validar_disponibilidad(clase, socio_id, clase_id)

        doc = {
            "socioId": socio_id,
            "claseId": clase_id,
            "estado": "CONFIRMADA",
            "activo": True,
            "fechaBaja": None,
        }
        return self.repo.insert(doc)

    def listar(self, skip: int, limit: int, socio_id: str | None, clase_id: str | None, estado: str | None) -> list[dict]:
        filtro: dict = {}
        if socio_id:
            filtro["socioId"] = to_object_id(socio_id, "socioId")
        if clase_id:
            filtro["claseId"] = to_object_id(clase_id, "claseId")
        if estado:
            filtro["estado"] = estado
        return self.repo.find_active(filtro, skip=skip, limit=limit)

    def obtener(self, reserva_id: str) -> dict:
        reserva = self.repo.find_active_by_id(to_object_id(reserva_id, "id de reserva"))
        if reserva is None:
            raise NotFoundError("Reserva no encontrada")
        return reserva

    def actualizar(self, reserva_id: str, datos: ReservaUpdate) -> dict:
        oid = to_object_id(reserva_id, "id de reserva")
        reserva = self.repo.find_active_by_id(oid)
        if reserva is None:
            raise NotFoundError("Reserva no encontrada")

        cambios = datos.model_dump(exclude_none=True)
        if not cambios:
            raise BadRequestError("No se enviaron campos para actualizar")

        # Reactivar una reserva cancelada vuelve a ocupar un lugar: hay que revalidar clase y cupo.
        if cambios["estado"] == "CONFIRMADA" and reserva["estado"] != "CONFIRMADA":
            clase = self.clases.find_active_by_id(reserva["claseId"])
            if clase is None:
                raise BusinessRuleError("La clase de esta reserva fue dada de baja")
            self._validar_disponibilidad(clase, reserva["socioId"], reserva["claseId"], excluir_id=oid)

        actualizada = self.repo.update_active(oid, cambios)
        if actualizada is None:
            raise NotFoundError("Reserva no encontrada")
        return actualizada

    def eliminar(self, reserva_id: str) -> dict:
        """Baja lógica: activo=False y fechaBaja=ahora. (Cancelar es otra cosa: estado=CANCELADA vía PATCH.)"""
        reserva = self.repo.soft_delete(to_object_id(reserva_id, "id de reserva"))
        if reserva is None:
            raise NotFoundError("Reserva no encontrada")
        return reserva

    def _validar_disponibilidad(
        self, clase: dict, socio_id: ObjectId, clase_id: ObjectId, excluir_id: ObjectId | None = None
    ) -> None:
        if self.repo.find_confirmada(socio_id, clase_id, excluir_id) is not None:
            raise ConflictError("El socio ya tiene una reserva confirmada para esta clase")
        if self.repo.count_confirmadas(clase_id, excluir_id) >= clase["cupoMaximo"]:
            raise ConflictError("La clase no tiene cupo disponible")
