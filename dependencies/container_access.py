from fastapi import Depends, Request, HTTPException
from functools import wraps
from typing import Callable
from processors.query_executor import QueryExecutor
from app import get_query_executor
from routes.auth import get_current_user



from fastapi import Depends

async def require_container_access(
    request: Request,
    current_user: dict = Depends(get_current_user),  # ← вот здесь!
    query_executor: QueryExecutor = Depends(get_query_executor)
):
    user_id = current_user.get("user_id")
    user_role = current_user.get("user_role")

    container_id = None
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.json()
        container_id = body.get("container_id")
    elif "container_id" in request.query_params:
        container_id = request.query_params.get("container_id")
    elif "container_id" in request.path_params:
        container_id = request.path_params.get("container_id")

    if not container_id:
        raise HTTPException(status_code=400, detail="container_id обязателен для проверки доступа")

    if user_role != "admin":
        result = await query_executor.containers.db.fetch_one(
            "SELECT COUNT(*) FROM containers WHERE container_id = %s AND created_by_id = %s",
            (int(container_id), user_id)
        )
        if result[0] == 0:
            raise HTTPException(status_code=403, detail="Недостаточно прав для доступа к этому контейнеру")
