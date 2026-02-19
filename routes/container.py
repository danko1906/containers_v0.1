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
from datetime import datetime

#20.02.26 выгрузить EXCEL перечень контейнеров
from typing import Optional, Literal


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

#20.02.26 выгрузить EXCEL перечень контейнеров
class BulkDownloadRequest(BaseModel):
    # 1) Ручной выбор (чекбоксы)
    container_ids: Optional[List[int]] = None

    # 2) Диапазон ID
    container_id_from: Optional[int] = None
    container_id_to: Optional[int] = None

    # 3) Диапазон дат packed_date
    packed_date_from: Optional[str] = None  # "2026-02-01 00:00:00" или "2026-02-01"
    packed_date_to: Optional[str] = None

    # Порядок для диапазонов
    order_by: Literal["container_id", "packed_date", "container_name"] = "container_id"
    order_dir: Literal["asc", "desc"] = "asc"

    # (опционально) порядок внутри контейнера
    sort_articles: Literal["asc", "desc"] = "asc"
    sort_dms: Literal["asc", "desc"] = "asc"

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


#20.02.26 выгрузить EXCEL перечень контейнеров
@container_router.post("/download_bulk")
async def download_containers_bulk_single_sheet_endpoint(
    data: BulkDownloadRequest,
    background_tasks: BackgroundTasks,
    query_executor: QueryExecutor = Depends(get_query_executor),
    current_user: str = Depends(get_current_user)  # Проверка авторизации
):
    try:
        user_id = current_user["user_id"]
        user_role = current_user["user_role"]

        # --- 1) Собираем список container_id по фильтру ---
        ids: List[int] = []

        # A) Ручной список
        if data.container_ids:
            ids = [int(x) for x in data.container_ids]

        # B) Диапазон ID
        elif data.container_id_from is not None and data.container_id_to is not None:
            a = int(data.container_id_from)
            b = int(data.container_id_to)
            if a > b:
                a, b = b, a  # чтобы BETWEEN работал

            order_by = data.order_by
            order_dir = data.order_dir.upper()
            if order_dir not in ("ASC", "DESC"):
                order_dir = "ASC"

            allowed_order = {"container_id", "packed_date", "container_name"}
            if order_by not in allowed_order:
                order_by = "container_id"

            rows = await query_executor.containers.db.fetch_all(
                f"""
                SELECT container_id
                FROM containers
                WHERE container_id BETWEEN %s AND %s
                ORDER BY {order_by} {order_dir}
                """,
                (a, b),
            )
            ids = [int(r[0]) for r in rows]

        # C) Диапазон packed_date
        elif data.packed_date_from and data.packed_date_to:
            # fromisoformat понимает "YYYY-MM-DD" и "YYYY-MM-DD HH:MM:SS"
            dt_from = datetime.fromisoformat(data.packed_date_from)
            dt_to = datetime.fromisoformat(data.packed_date_to)

            order_by = data.order_by
            order_dir = data.order_dir.upper()
            if order_dir not in ("ASC", "DESC"):
                order_dir = "ASC"

            allowed_order = {"container_id", "packed_date", "container_name"}
            if order_by not in allowed_order:
                order_by = "packed_date"

            rows = await query_executor.containers.db.fetch_all(
                f"""
                SELECT container_id
                FROM containers
                WHERE packed_date BETWEEN %s AND %s
                ORDER BY {order_by} {order_dir}
                """,
                (dt_from, dt_to),
            )
            ids = [int(r[0]) for r in rows]

        else:
            raise HTTPException(status_code=400, detail="Передай container_ids ИЛИ диапазон container_id_from/to ИЛИ packed_date_from/to")

        if not ids:
            raise HTTPException(status_code=404, detail="По заданному фильтру контейнеры не найдены")

        # --- 2) Проверка прав (как require_container_access, но для списка) ---
        if user_role != "admin":
            placeholders = ", ".join(["%s"] * len(ids))
            rows = await query_executor.containers.db.fetch_all(
                f"""
                SELECT container_id
                FROM containers
                WHERE created_by_id = %s AND container_id IN ({placeholders})
                """,
                tuple([user_id] + ids),
            )
            allowed = {int(r[0]) for r in rows}
            denied = [cid for cid in ids if cid not in allowed]
            if denied:
                raise HTTPException(status_code=403, detail=f"Недостаточно прав для контейнеров: {denied}")

        # --- 3) Подтянем packed_date одним запросом (чтобы вывести в Excel) ---
        placeholders = ", ".join(["%s"] * len(ids))
        packed_rows = await query_executor.containers.db.fetch_all(
            f"""
            SELECT container_id, packed_date
            FROM containers
            WHERE container_id IN ({placeholders})
            """,
            tuple(ids),
        )
        packed_map = {}
        for cid, pdate in packed_rows:
            if pdate:
                packed_map[int(cid)] = pdate.strftime("%Y-%m-%d %H:%M:%S")
            else:
                packed_map[int(cid)] = ""

        # --- 4) Собираем kits и добавляем packed_date ---
        kits = []
        for cid in ids:
            kit = await query_executor.containers.get_container_kit(cid)
            if not kit.get("success"):
                raise HTTPException(status_code=400, detail=f"Не удалось собрать kit для container_id={cid}")
            kit["packed_date"] = packed_map.get(int(cid), "")
            kits.append(kit)

        # --- 5) Генерируем 1 Excel / 1 лист / 1 таблица ---
        file_path, file_name = await ExcelProcessor.create_excel_file_bulk_single_sheet(
            kits,
            file_prefix="containers_bulk_",
            order_by=data.order_by,
            order_dir=data.order_dir,
            sort_articles=data.sort_articles,
            sort_dms=data.sort_dms,
        )

        background_tasks.add_task(remove_file, file_path)

        return FileResponse(path=file_path, filename=file_name, media_type="application/octet-stream")

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error bulk download: {str(e)}")
        raise HTTPException(status_code=500, detail=ERROR_RETRIEVE_CONTAINER_KIT)
