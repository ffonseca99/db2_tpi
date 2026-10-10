"""Configuración de la aplicación (se lee desde variables de entorno / archivo .env)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    mongo_uri: str
    db_name: str


def get_settings() -> Settings:
    uri = os.getenv("MONGO_URI")
    if not uri:
        raise RuntimeError(
            "Falta la variable de entorno MONGO_URI. "
            "Copiá .env.example como .env y completá la cadena de conexión."
        )
    return Settings(mongo_uri=uri, db_name=os.getenv("DB_NAME", "gimnasio"))
