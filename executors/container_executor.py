import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from processors.dict_processor import consolidate_dm_by_article
from executors.dm_executor import DMExecutor
from message.engish_message import *

class ContainerExecutor:
    def __init__(self, db, dm_executor: DMExecutor):
        self.db = db
        self.dm_executor = dm_executor

    async def get_dm_status_and_info(self, dm_without_tail: str) -> Dict[str, Any]:
        try:
            # Получаем информацию о DM-коде через DMExecutor
            dm_info_result = await self.dm_executor.get_dm_info_by_codes([dm_without_tail])
            if not dm_info_result.get("success") or not dm_info_result.get("dm_info"):
                return {"success": False, "message": DM_NOT_FOUND}

            dm_data = dm_info_result["dm_info"][0]
            article = dm_data["article"]
            invoice_date = dm_data["invoice_date"]
            current_page_num = dm_data["current_page_num"]

            # Проверяем, привязан ли DM к какому-либо контейнеру
            container_query = """
                SELECT c.container_id, c.container_name, c.container_status, c.packed_date
                FROM dm_in_containers dic
                JOIN containers c ON dic.container_id = c.container_id
                WHERE dic.dm_without_tail = %s
            """
            container_info = await self.db.fetch_one(container_query, (dm_without_tail,))

            if container_info:
                container_id, container_name, container_status, packed_date = container_info
                status = "packed"
                container_details = {
                    "container_id": container_id,
                    "container_name": container_name,
                    "container_status": container_status,
                    "packed_date": packed_date.strftime("%Y-%m-%d %H:%M:%S") if packed_date else None
                }
            else:
                status = "non_packed"
                container_details = {}

            return {
                "success": True,
                "data": {
                    "article": article,
                    "invoice_date": invoice_date,
                    "current_page_num": current_page_num,
                    "status": status,
                    "container_info": container_details
                }
            }
        except Exception as e:
            logging.error(f"Error fetching DM status and info: {e}")
            return {"success": False, "message": ERROR_FETCH_DM_INFO}

    async def create_container(self, container_name: str, created_by_id: int) -> Dict[str, Any]:
        try:
            existing_container = await self.db.fetch_one(
                "SELECT container_id FROM containers WHERE container_name = %s", (container_name,))
            if existing_container:
                return {"success": False, "message": CONTAINER_ALREADY_EXISTS}

            # Вставляем контейнер с созданием нового ID и привязкой к созданию через created_by_id
            await self.db.fetch_one(
                "INSERT INTO containers (container_name, container_status, created_by_id) VALUES (%s, %s, %s)",
                (container_name, "new", created_by_id)
            )

            # Получаем ID нового контейнера
            new_container_id = await self.db.fetch_one("SELECT LAST_INSERT_ID()")

            return {
                "success": True,
                "message": CONTAINER_CREATED.format(container_name),
                "container_id": new_container_id[0],
                "container_name": container_name
            }
        except Exception as e:
            logging.error(f"Error creating container: {e}")
            return {"success": False, "message": ERROR_CREATE_CONTAINER}

    async def get_containers(
            self,
            container_statuses: List[str],
            user_role: str,
            created_by_id: Optional[int] = None
    ) -> Dict[str, Any]:
        base_query = """
            SELECT container_id, container_name, container_status
            FROM containers
        """
        query = base_query
        conditions = []
        params = []

        if user_role == 'admin':
            # Только фильтр по статусам, если указан
            if container_statuses:
                placeholders = ", ".join(["%s"] * len(container_statuses))
                conditions.append(f"container_status IN ({placeholders})")
                params.extend(container_statuses)

        elif user_role == 'warehouseman':
            # Фильтр по статусам и автору (обязателен created_by_id)
            if container_statuses:
                placeholders = ", ".join(["%s"] * len(container_statuses))
                conditions.append(f"container_status IN ({placeholders})")
                params.extend(container_statuses)

            if created_by_id is not None:
                conditions.append("created_by_id = %s")
                params.append(created_by_id)
            else:
                return {"success": False, "message": "created_by_id is required for warehouseman"}

        else:
            return {"success": False, "message": f"Unknown user role: {user_role}"}

        # Добавление условий в запрос
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        try:
            rows = await self.db.fetch_all(query, params)
            containers = [
                {"container_id": row[0], "container_name": row[1], "container_status": row[2]}
                for row in rows
            ]
            return {"success": True, "containers": containers}
        except Exception as e:
            logging.error(f"Error fetching containers: {e}")
            return {"success": False, "message": ERROR_FETCH_CONTAINERS}

    async def rename_container(self, container_id: int, new_container_name: str) -> Dict[str, Any]:
        try:
            count = await self.db.fetch_one(
                "SELECT COUNT(*) FROM containers WHERE container_name = %s", (new_container_name,)
            )
            if count[0] > 0:
                return {"success": False, "message": CONTAINER_ALREADY_EXISTS}

            await self.db.fetch_one(
                "UPDATE containers SET container_name = %s WHERE container_id = %s", (new_container_name, container_id)
            )
            return {"success": True, "message": CONTAINER_RENAMED}
        except Exception as e:
            logging.error(f"Error renaming container: {e}")
            return {"success": False, "message": ERROR_RENAME_CONTAINER}

    async def add_dm_code(self, dm_without_tail: str, container_id: int, packed_by_id: int) -> Dict[str, Any]:
        try:
            # Проверка существования DM-кода
            check_result = await self.dm_executor.check_dm_code_exists(dm_without_tail)
            if not check_result["success"]:
                return {"success": False, "message": CODE_NOT_FOUND}

            # Проверка: не был ли этот DM-код уже добавлен
            existing_dm = await self.db.fetch_one(
                "SELECT container_id FROM dm_in_containers WHERE dm_without_tail = %s", (dm_without_tail,)
            )
            if existing_dm:
                container_name = await self.db.fetch_one(
                    "SELECT container_name FROM containers WHERE container_id = %s", (existing_dm[0],)
                )
                return {
                    "success": False,
                    "message": CODE_ALREADY_ADDED.format(container_name=container_name[0])
                }

            # Вставка DM-кода в контейнер с указанием packed_by_id
            await self.db.fetch_one(
                """
                INSERT INTO dm_in_containers (dm_without_tail, container_id, packed_by_id)
                VALUES (%s, %s, %s)
                """,
                (dm_without_tail, container_id, packed_by_id)
            )

            # Обновление статуса контейнера на 'packing'
            await self.db.fetch_one(
                "UPDATE containers SET container_status = 'packing' WHERE container_id = %s",
                (container_id,)
            )

            return {"success": True, "message": CODE_ADDED_SUCCESS}

        except Exception as e:
            logging.error(f"Error adding DM code: {e}")
            return {"success": False, "message": ERROR_ADD_DM_CODE}


    async def get_container_name_by_id(self, container_id: int) -> Dict[str, Any]:
        try:
            result = await self.db.fetch_one(
                "SELECT container_name, container_status FROM containers WHERE container_id = %s", (container_id,)
            )
            if result:
                return {"success": True, "container_name": result[0], "container_status": result[1]}
            else:
                return {"success": False, "message": CONTAINER_NOT_FOUND.format(container_id=container_id)}
        except Exception as e:
            logging.error(f"Error fetching container name: {e}")
            return {"success": False, "message": ERROR_FETCH_CONTAINER_NAME}

    async def get_dm_codes_by_container(self, container_id: int) -> Dict[str, Any]:
        query = "SELECT dm_without_tail FROM dm_in_containers WHERE container_id = %s"
        try:
            rows = await self.db.fetch_all(query, (container_id,))
            return {"success": True, "dm_codes": [row[0] for row in rows]}
        except Exception as e:
            logging.error(f"Error fetching DM codes: {e}")
            return {"success": False, "message": ERROR_FETCH_DM_CODES}

    async def update_container_status_to_packed(self, container_id: int) -> Dict[str, Any]:
        try:
            packed_date = datetime.now()
            container = await self.db.fetch_one("SELECT container_id FROM containers WHERE container_id = %s", (container_id,))
            if not container:
                return {"success": False, "message": CONTAINER_NOT_FOUND.format(container_id=container_id)}
            await self.db.fetch_one("UPDATE containers SET container_status = %s, packed_date = %s WHERE container_id = %s", ('packed', packed_date, container_id))
            return {"success": True, "message": CONTAINER_UPDATE_SUCCESS.format(container_id=container_id)}
        except Exception as e:
            logging.error(f"Error updating container status: {e}")
            return {"success": False, "message": ERROR_UPDATE_CONTAINER_STATUS}

    async def remove_dm_code_from_container(self, dm_without_tail: str, container_id: int) -> Dict[str, Any]:
        try:
            existing_dm = await self.db.fetch_one("SELECT container_id FROM dm_in_containers WHERE dm_without_tail = %s AND container_id = %s", (dm_without_tail, container_id))
            if not existing_dm:
                return {"success": False, "message": DM_CODE_NOT_FOUND}
            await self.db.fetch_one("DELETE FROM dm_in_containers WHERE dm_without_tail = %s AND container_id = %s", (dm_without_tail, container_id))
            remaining_dm_count = await self.db.fetch_one("SELECT COUNT(*) FROM dm_in_containers WHERE container_id = %s", (container_id,))
            if remaining_dm_count[0] == 0:
                await self.db.fetch_one("UPDATE containers SET container_status = 'new' WHERE container_id = %s", (container_id,))
            return {"success": True, "message": DM_CODE_REMOVED}
        except Exception as e:
            logging.error(f"Error removing DM code: {e}")
            return {"success": False, "message": ERROR_REMOVE_DM_CODE}

    async def delete_container_and_dms(self, container_id: int) -> Dict[str, Any]:
        try:
            container_name_result = await self.get_container_name_by_id(container_id)
            if not container_name_result.get("success"):
                return {"success": False, "message": CONTAINER_NOT_FOUND.format(container_id=container_id)}
            container_name = container_name_result["container_name"]
            container_status = await self.db.fetch_one("SELECT container_status FROM containers WHERE container_id = %s", (container_id,))
            if not container_status or container_status[0] != 'new':
                return {"success": False, "message": CONTAINER_CANNOT_BE_DELETED_STATUS.format(container_id=container_id)}
            dm_codes_in_container = await self.db.fetch_one("SELECT COUNT(*) FROM dm_in_containers WHERE container_id = %s", (container_id,))
            if dm_codes_in_container[0] > 0:
                return {"success": False, "message": CONTAINER_CANNOT_BE_DELETED_DMS.format(container_id=container_id)}
            await self.db.fetch_one("DELETE FROM containers WHERE container_id = %s", (container_id,))
            logging.info(CONTAINER_DELETED.format(container_name=container_name, container_id=container_id))
            return {"success": True, "message": CONTAINER_DELETED.format(container_name=container_name, container_id=container_id)}
        except Exception as e:
            logging.error(f"Error deleting container: {e}")
            return {"success": False, "message": ERROR_DELETE_CONTAINER}

    async def get_container_kit(self, container_id: int) -> Dict[str, Any]:
        try:
            container_name_result = await self.get_container_name_by_id(container_id)
            if not container_name_result.get("success"):
                return container_name_result

            if container_name_result.get("container_status") == "new":
                return {
                    "success": True,
                    "container_id": container_id,
                    "container_name": container_name_result["container_name"],
                    "container_status": container_name_result.get("container_status"),
                    "scanned": []
                }

            dm_codes_result = await self.get_dm_codes_by_container(container_id)
            if not dm_codes_result.get("success"):
                return dm_codes_result

            dm_info_result = await self.dm_executor.get_dm_info_by_codes(dm_codes_result["dm_codes"])
            if not dm_info_result.get("success"):
                return dm_info_result

            scanned = await consolidate_dm_by_article(dm_info_result["dm_info"])
            return {
                "success": True,
                "container_id": container_id,
                "container_name": container_name_result["container_name"],
                "container_status": container_name_result.get("container_status"),
                "scanned": scanned
            }
        except Exception as e:
            logging.error(f"Error generating container kit: {e}")
            return {"success": False, "message": ERROR_GENERATE_CONTAINER_KIT}
