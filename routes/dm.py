from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from processors.query_executor import QueryExecutor
from app import get_query_executor
from routes.auth import get_current_user
from dependencies.container_access import require_container_access
from message.engish_message import *

# Создание экземпляра роутера FastAPI
dm_router = APIRouter()

class DMStatusRequest(BaseModel):
    dm_without_tail: str

# Путь для получения информации
# Pydantic-модель для валидации входящих данных
class AddDMRequest(BaseModel):
    dm_without_tail: str
    container_id: int

# Путь для добавления DM-кода в контейнер
# Путь для добавления DM-кода в контейнер
@dm_router.post("/add")
async def add_dm(
        request: AddDMRequest,
        query_executor: QueryExecutor = Depends(get_query_executor),
        _: None = Depends(require_container_access),
        current_user: str = Depends(get_current_user)  # Проверка авторизации
):
    try:
        dm_without_tail = request.dm_without_tail
        container_id = request.container_id
        user_id = current_user["user_id"]

        container_name_result = await query_executor.containers.get_container_name_by_id(container_id=container_id)
        if not container_name_result.get("success"):
            return JSONResponse(
                content={"success": False, "message": ERROR_CONTAINER_NOT_FOUND},
                status_code=404
            )

        dm_add_result = await query_executor.containers.add_dm_code(dm_without_tail=dm_without_tail,
                                                                    container_id=container_id, packed_by_id=user_id)
        if not dm_add_result.get("success"):
            return JSONResponse(content=dm_add_result, status_code=400)

        result = await query_executor.containers.get_container_kit(container_id)
        return JSONResponse(content={"success": True, "container_kit": result}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=ERROR_INTERNAL_SERVER.format(error_message=str(e)))


@dm_router.post("/info")
async def get_dm_status_info(
        request: DMStatusRequest,
        query_executor: QueryExecutor = Depends(get_query_executor),
        current_user: str = Depends(get_current_user)  # Проверка авторизации
):
    try:
        dm_without_tail = request.dm_without_tail

        dm_status_result = await query_executor.containers.get_dm_status_and_info(dm_without_tail)
        if not dm_status_result.get("success"):
            return JSONResponse(content=dm_status_result, status_code=404)

        return JSONResponse(content=dm_status_result, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=ERROR_INTERNAL_SERVER.format(error_message=str(e)))


# Путь для удаления DM-кода из контейнера
@dm_router.post("/delete")
async def delete_dm(
        request: AddDMRequest,
        query_executor: QueryExecutor = Depends(get_query_executor),
        _: None = Depends(require_container_access),
        current_user: str = Depends(get_current_user)  # Проверка авторизации
):
    try:
        dm_without_tail = request.dm_without_tail
        container_id = request.container_id

        container_name_result = await query_executor.containers.get_container_name_by_id(container_id)
        if not container_name_result.get("success"):
            return JSONResponse(content={"success": False, "message": ERROR_CONTAINER_NOT_FOUND}, status_code=404)

        delete_result = await query_executor.containers.remove_dm_code_from_container(dm_without_tail, container_id)
        if not delete_result.get("success"):
            return JSONResponse(content=delete_result, status_code=400)

        result = await query_executor.containers.get_container_kit(container_id)
        return JSONResponse(content={"success": True, "container_kit": result}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=ERROR_INTERNAL_SERVER.format(error_message=str(e)))