import aiomysql
from typing import Optional

class Database:
    def __init__(self, config):
        self.config = config
        self.pool: Optional[aiomysql.Pool] = None

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
                is_write_operation = query.strip().upper().startswith(
                    ('INSERT', 'UPDATE', 'DELETE', 'REPLACE')
                )
                if is_write_operation:
                    await connection.commit()
                return await cursor.fetchone() if fetchone else await cursor.fetchall()
