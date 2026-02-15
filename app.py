from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import Config
from executors.database import Database
from executors.querry_executor import QueryExecutor
from fastapi import Depends
from typing import Tuple
from executors.dm_executor import DMExecutor
from executors.user_executor import UserExecutor
from executors.container_executor import ContainerExecutor




# Создание экземпляра базы данных
dm_db = Database(Config.DM_DB_CONFIG)
cnt_db=Database(Config.CNT_DB_CONFIG)
user_db=Database(Config.USER_DB_CONFIG)



# Lifespan для управления событиями
async def lifespan(app: FastAPI):
    # Инициализация базы данных
    try:
        await dm_db.initialize()
        await cnt_db.initialize()
        await user_db.initialize()
        print("Database connection initialized")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise

    yield

    # Закрытие подключения к базе данных
    await dm_db.close()
    await cnt_db.close()
    await user_db.close()
    print("Database connection closed")

# Функция для создания зависимости QueryExecutor
def get_db() -> Tuple[Database, Database, Database]:
    return dm_db, cnt_db, user_db

# Используем зависимости, распаковываем и передаём в QueryExecutor
def get_query_executor(dbs: Tuple[Database, Database, Database] = Depends(get_db)) -> QueryExecutor:
    dm, cnt, user = dbs
    dm_executor=DMExecutor(dm)
    user_executor=UserExecutor(user)
    container_executor=ContainerExecutor(db=cnt, dm_executor=dm_executor)
    return QueryExecutor(
        dm_executor=dm_executor,
        container_executor=container_executor,
        user_executor=user_executor
    )

# Создание экземпляра FastAPI с использованием Lifespan
def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    # Настройка CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
