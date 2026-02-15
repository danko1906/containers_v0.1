import aiomysql
from typing import Optional

class Database:
    _instance: Optional["Database"] = None

    def __new__(cls, config):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config = config
            cls._instance.pool = None
        return cls._instance

    async def initialize(self):
        if not self.pool:
            self.pool = await aiomysql.create_pool(**self.config)

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def fetch_one(self, query, params=None):
        return await self._execute_query(query, params, fetchone=True)

    async def fetch_all(self, query, params):
        return await self._execute_query(query, params, fetchone=False)

    async def _execute_query(self, query, params=None, fetchone=True):
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(query, params)
                # Определяем, является ли запрос модифицирующим
                is_write_operation = query.strip().upper().startswith(
                    ('INSERT', 'UPDATE', 'DELETE', 'REPLACE')
                )
                if is_write_operation:
                    await connection.commit()
                else:
                    # Для чтения можно сразу закрывать
                    await connection.commit()  # или оставить как есть, зависит от логики
                return await cursor.fetchone() if fetchone else await cursor.fetchall()