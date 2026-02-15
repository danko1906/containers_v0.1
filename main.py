from routes.auth import auth_router, get_current_user
from routes.container import container_router
from routes.dm import dm_router
from routes.user import user_router
from app import create_app, get_query_executor
from fastapi import Depends
from config import Config

app = create_app()

# Регистрация маршрутов, зависимости QueryExecutor теперь передается автоматически
app.include_router(auth_router, prefix='/api/auth', dependencies=[Depends(get_query_executor)])
app.include_router(container_router, prefix='/api/containers', dependencies=[Depends(get_query_executor), Depends(get_current_user)])
app.include_router(user_router, prefix='/api/user', dependencies=[Depends(get_current_user)])
app.include_router(dm_router, prefix='/api/dm', dependencies=[Depends(get_query_executor), Depends(get_current_user)])

# Запуск приложения с uvicorn
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=Config.host, port=Config.port)
