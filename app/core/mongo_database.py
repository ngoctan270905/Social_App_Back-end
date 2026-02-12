import logging
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from .config import settings

logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(self):
        self.client: AsyncMongoClient | None = None
        self._database: AsyncDatabase | None = None

    # async connect
    async def connect(self):
        if self.client is None:
            self.client = AsyncMongoClient(settings.MONGO_CONNECTION_STRING)
            self._database = self.client.get_database(settings.MONGO_DB_NAME)
            await self.client.admin.command("ping")
            logger.info("Ket noi toi MongoDB thanh cong")

    # async close
    async def close(self):
        if self.client:
            await self.client.close()
            self.client = None
            self._database = None
            logger.info("Da dong ket noi voi MongoDB")

    # get database
    def get_database(self) -> AsyncDatabase:
        if self._database is None:
            raise Exception("Chua ket noi toi MongoDB")
        return self._database

mongodb_client = MongoDBClient()