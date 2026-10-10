from pymongo.database import Database

from app.repositories.base import BaseRepository


class ClaseRepository(BaseRepository):
    def __init__(self, db: Database):
        super().__init__(db.clases)
