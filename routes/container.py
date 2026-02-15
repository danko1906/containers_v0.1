import os
import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List
from executors.querry_executor import QueryExecutor
from app import get_query_executor
from processors.excel_processor import ExcelProcessor
from routes.auth import get_current_user
from dependencies.container_access import require_container_access
from message.engish_message import *  # Import constants from messages.py


container_router = APIRouter()


class nameContainer(BaseModel):
    container_name: str


class numberContainer(BaseModel):
    container_id: int

class statusesContainer(BaseModel):
    container_statuses: List[str]

class renameContainer(BaseModel):
    container_id: int
    new_container_name: str


async def remove_file(path: str):
    os.remove(path)

@container_router.post("/create")
async def create_container_endpoint(
        data: nameContainer,
        query_executor: QueryExecutor = Depends(get_query_executor),
        current_user: str = Depends(get_current_user)  # Проверка авторизации
):
    try:
        container_name = data.container_name
        user_id = current_user["user_id"]
        result = await query_executor.containers.create_container(container_name=container_name, created_by_id=user_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result)

        return JSONResponse(content=result, status_code=200)

    except Exception as e:
        logging.error(f"Ошибка создания контейнера: {str(e)}")
        raise HTTPException(status_code=500, detail=ERROR_CREATE_CONTAINER)


@container_router.post("/get")
async def get_containers_endpoint(
        data: statusesContainer,
        query_executor: QueryExecutor = Depends(get_query_executor),
        current_user: str = Depends(get_current_user)  # Проверка авторизации
):
    user_id = current_user["user_id"]
    user_role = current_user["user_role"]

    try:
        container_statuses = data.container_statuses
        containers = await query_executor.containers.get_containers(container_statuses=container_statuses, created_by_id=user_id, user_role=user_role)
        return JSONResponse(content={"success": True, "containers": containers}, status_code=200)

    except Exception as e:
        logging.error(f"Ошибка получения контейнеров: {str(e)}")
        raise HTTPException(status_code=500, detail=ERROR_GET_CONTAINERS)


@container_router.post("/delete")
async def delete_container_endpoint(
        data: numberContainer,
        _: None = Depends(require_container_access),
        query_executor: QueryExecutor = Depends(get_query_executor),
        current_user: str = Depends(get_current_user)  # Проверка авторизации
):
    try:
        container_id = data.container_id
        result = await query_executor.containers.delete_container_and_dms(container_id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return JSONResponse(content={"success": True, "message": SUCCESS_CONTAINER_DELETED}, status_code=200)

    except Exception as e:
        logging.error(f"Ошибка удаления контейнера: {str(e)}")
        raise HTTPException(status_code=500, detail=ERROR_DELETE_CONTAINER)


@container_router.post("/packed")
async def packed_container_endpoint(
        data: numberContainer,
        _: None = Depends(require_container_access),
        query_executor: QueryExecutor = Depends(get_query_executor),
        current_user: str = Depends(get_current_user)  # Проверка авторизации
):
    try:
        container_id = data.container_id
        result = await query_executor.containers.update_container_status_to_packed(container_id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return JSONResponse(content={"success": True, "message": SUCCESS_CONTAINER_PACKED}, status_code=200)

    except Exception as e:
        logging.error(f"Ошибка удаления контейнера: {str(e)}")
        raise HTTPException(status_code=500, detail=ERROR_PACKED_CONTAINER)


@container_router.put("/rename")
async def rename_container_endpoint(
        data: renameContainer,
        _: None = Depends(require_container_access),
        query_executor: QueryExecutor = Depends(get_query_executor),
        current_user: str = Depends(get_current_user)  # Проверка авторизации
):
    try:
        new_container_name = data.new_container_name
        container_id = data.container_id
        result = await query_executor.containers.rename_container(container_id, new_container_name)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return JSONResponse(content={"success": True, "message": SUCCESS_CONTAINER_RENAMED}, status_code=200)

    except Exception as e:
        logging.error(f"Ошибка переименования контейнера: {str(e)}")
        raise HTTPException(status_code=500, detail=ERROR_RENAME_CONTAINER)


@container_router.post("/kit")
async def get_container_kit_endpoint(
        data: numberContainer,
        _: None = Depends(require_container_access),
        query_executor: QueryExecutor = Depends(get_query_executor),
        current_user: str = Depends(get_current_user)  # Проверка авторизации
):
    try:
        container_id = data.container_id
        result = await query_executor.containers.get_container_kit(container_id)
        return JSONResponse(content={"success": True, "container_kit": result}, status_code=200)

    except Exception as e:
        logging.error(f"Ошибка получения комплектации контейнера: {str(e)}")
        raise HTTPException(status_code=500, detail=ERROR_GET_CONTAINER_KIT)


@container_router.post("/download")
async def download_container_kit_endpoint(
        data: numberContainer,
        background_tasks: BackgroundTasks,
        _: None = Depends(require_container_access),
        query_executor: QueryExecutor = Depends(get_query_executor),
        current_user: str = Depends(get_current_user)  # Проверка авторизации
):
    try:
        container_id = data.container_id
        kit = await query_executor.containers.get_container_kit(container_id)

        file_path, file_name = await ExcelProcessor.create_excel_file(data=kit)

        # Schedule file removal after download
        background_tasks.add_task(remove_file, file_path)

        return FileResponse(path=file_path, filename=file_name, media_type="application/octet-stream")

    except Exception as e:
        logging.error(f"Error retrieving container kit: {str(e)}")
        raise HTTPException(status_code=500, detail=ERROR_RETRIEVE_CONTAINER_KIT)
