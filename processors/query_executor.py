import bcrypt
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from processors.dict_processor import consolidate_dm_by_article

ERROR_FETCH_DM_INFO = "Error fetching DM code information."
ERROR_FETCH_USER = "Error fetching user."
ERROR_CREATE_USER = "Error creating user."
ERROR_VERIFY_PASSWORD = "Error verifying password."
ERROR_CREATE_CONTAINER = "An error occurred while creating the container."
ERROR_FETCH_CONTAINERS = "Error fetching the list of containers."
ERROR_RENAME_CONTAINER = "Error renaming container."
DM_NOT_FOUND = "DM code not found in the dm_info table."
USER_NOT_FOUND = "User not found."
USER_ALREADY_EXISTS = "A user with this login already exists."
PASSWORD_CORRECT = "Password is correct."
PASSWORD_INCORRECT = "Incorrect password."
CONTAINER_ALREADY_EXISTS = "A container with this name already exists."
CONTAINER_CREATED = "Container {} successfully created."
CONTAINER_RENAMED = "Container successfully renamed."
USER_CREATED = "User successfully created."
ERROR_ADD_DM_CODE = "Error adding DM code."
ERROR_FETCH_CONTAINER_NAME = "Error fetching container name."
CODE_NOT_FOUND = "This code was not found."
CODE_ALREADY_ADDED = "Code already added to {container_name}."
CODE_ADDED_SUCCESS = "Code successfully added to the container and container status updated."
CONTAINER_NOT_FOUND = "Container with ID {container_id} not found."
ERROR_FETCH_DM_CODES = "Error fetching DM codes."
ERROR_UPDATE_CONTAINER_STATUS = "Error updating container status."
ERROR_GENERATE_CONTAINER_KIT = "Error generating container kit."
ERROR_REMOVE_DM_CODE = "Error removing DM code from the container."
ERROR_DELETE_CONTAINER = "Error deleting container."
CONTAINER_UPDATE_SUCCESS = "Container with ID {container_id} successfully updated to status 'packed'."
DM_CODE_NOT_FOUND = "DM code not found in the container."
DM_CODE_REMOVED = "DM code successfully removed from the container."
CONTAINER_CANNOT_BE_DELETED_STATUS = "Container with ID {container_id} cannot be deleted because its status is not 'new'."
CONTAINER_CANNOT_BE_DELETED_DMS = "Container with ID {container_id} cannot be deleted because it contains DM codes."
CONTAINER_DELETED = "Container '{container_name}' (ID {container_id}) successfully deleted."

class QueryExecutor:

    def __init__(self, db):
        self.db = db

    async def get_dm_status_and_info(self, dm_without_tail: str) -> Dict[str, Any]:
        try:
            dm_query = """
                SELECT article, invoice_date, current_page_num
                FROM dm_info
                WHERE dm_without_tail = %s
            """
            dm_info = await self.db.fetch_one(dm_query, (dm_without_tail,))

            if not dm_info:
                return {"success": False, "message": DM_NOT_FOUND}

            article, invoice_date, current_page_num = dm_info

            container_query = """
                SELECT c.container_id, c.container_name, c.container_status, c.packed_date
                FROM dm_in_containers dic
                JOIN containers c ON dic.container_id = c.container_id
                WHERE dic.dm_without_tail = %s
            """
            container_info = await self.db.fetch_one(container_query, (dm_without_tail,))

            status, container_details = ("packed", {
                "container_name": container_info[1],
                "container_id": container_info[0],
                "container_status": container_info[2],
                "packed_date": container_info[3].strftime("%Y-%m-%d %H:%M:%S") if container_info[3] else None
            }) if container_info else ("non_packed", {})

            return {"success": True, "data": {
                "article": article,
                "invoice_date": invoice_date,
                "current_page_num": current_page_num,
                "status": status,
                "container_info": container_details
            }}
        except Exception as e:
            logging.error(f"Error fetching DM status and info: {e}")
            return {"success": False, "message": ERROR_FETCH_DM_INFO}

    async def get_user_by_login(self, login: str) -> Dict[str, Any]:
        try:
            query = "SELECT login, password_hash FROM users WHERE login = %s"
            user = await self.db.fetch_one(query, (login,))
            if user:
                return {"success": True, "user": {"login": user[0], "password_hash": user[1]}}
            return {"success": False, "message": USER_NOT_FOUND}
        except Exception as e:
            logging.error(f"Error fetching user by login: {e}")
            return {"success": False, "message": ERROR_FETCH_USER}

    async def create_user(self, login: str, password: str) -> Dict[str, Any]:
        try:
            existing_user = await self.get_user_by_login(login)
            if existing_user.get("success"):
                return {"success": False, "message": USER_ALREADY_EXISTS}

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            await self.db.fetch_one("INSERT INTO users (login, password_hash) VALUES (%s, %s)", (login, hashed_password))
            return {"success": True, "message": USER_CREATED}
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            return {"success": False, "message": ERROR_CREATE_USER}

    async def verify_user_password(self, login: str, password: str) -> bool:
        try:
            user = await self.get_user_by_login(login)
            if not user.get("success"):
                return False

            password_hash = user['user']['password_hash']
            if isinstance(password_hash, str):
                password_hash = password_hash.encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), password_hash):
                return True
            else:
                return False
        except Exception as e:
            logging.error(f"Error verifying user password: {e}")
            return False

    async def create_container(self, container_name: str) -> Dict[str, Any]:
        try:
            existing_container = await self.db.fetch_one("SELECT container_id FROM containers WHERE container_name = %s", (container_name,))
            if existing_container:
                return {"success": False, "message": CONTAINER_ALREADY_EXISTS}

            max_id = await self.db.fetch_one("SELECT MAX(container_id) FROM containers")
            new_container_id = (max_id[0] or 0) + 1

            await self.db.fetch_one("INSERT INTO containers (container_id, container_name, container_status) VALUES (%s, %s, %s)", (new_container_id, container_name, "new"))
            return {"success": True, "message": CONTAINER_CREATED.format(container_name), "container_id": new_container_id, "container_name": container_name}
        except Exception as e:
            logging.error(f"Error creating container: {e}")
            return {"success": False, "message": ERROR_CREATE_CONTAINER}

    async def get_containers(self, container_statuses: List[str]) -> Dict[str, Any]:
        query = """
            SELECT container_id, container_name, container_status
            FROM containers
        """
        params = []

        if container_statuses:
            query += " WHERE container_status IN ({})".format(", ".join(["%s"] * len(container_statuses)))
            params = container_statuses

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

    async def add_dm_code(self, dm_without_tail: str, container_id: int) -> Dict[str, Any]:
        try:
            dm_count = await self.db.fetch_one(
                "SELECT COUNT(*) FROM dm_info WHERE dm_without_tail = %s", (dm_without_tail,)
            )
            if dm_count[0] == 0:
                return {"success": False, "message": CODE_NOT_FOUND}

            existing_dm = await self.db.fetch_one(
                "SELECT container_id FROM dm_in_containers WHERE dm_without_tail = %s", (dm_without_tail,)
            )
            if existing_dm:
                container_name = await self.db.fetch_one(
                    "SELECT container_name FROM containers WHERE container_id = %s", (existing_dm[0],)
                )
                return {"success": False, "message": CODE_ALREADY_ADDED.format(container_name=container_name[0])}

            await self.db.fetch_one(
                "INSERT INTO dm_in_containers (dm_without_tail, container_id) VALUES (%s, %s)",
                (dm_without_tail, container_id)
            )
            await self.db.fetch_one(
                "UPDATE containers SET container_status = 'packing' WHERE container_id = %s", (container_id,)
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

    async def get_dm_info_by_codes(self, dm_codes: List[str]) -> Dict[str, Any]:
        query = """
               SELECT dm_without_tail, article, invoice_date, current_page_num
               FROM dm_info
               WHERE dm_without_tail IN (%s)
           """
        try:
            # Format the list of dm_codes as a comma-separated string of placeholders
            placeholders = ', '.join(['%s'] * len(dm_codes))  # Create a placeholder for each dm_code
            formatted_query = query % placeholders  # Replace (%s) with the actual placeholders

            # Execute the query with the list of dm_codes as the parameters
            rows = await self.db.fetch_all(formatted_query, tuple(dm_codes))

            dm_info = [
                {"dm_without_tail": row[0], "article": row[1], "invoice_date": row[2], "current_page_num": row[3]}
                for row in rows
            ]
            return {"success": True, "dm_info": dm_info}
        except Exception as e:
            logging.error(f"Error fetching DM info: {e}")
            return {"success": False, "message": DM_NOT_FOUND}


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


    async def get_container_kit(self, container_id: int) -> Dict[str, Any]:
        try:
            container_name_result = await self.get_container_name_by_id(container_id)

            if not container_name_result.get("success"):
                return container_name_result
            if container_name_result.get("container_status")=="new":
                result={
                "success": True,
                "container_id": container_id,
                "container_name": container_name_result["container_name"],
                "container_status": container_name_result.get("container_status"),
                "scanned": []
            }
                return result

            dm_codes_result = await self.get_dm_codes_by_container(container_id)
            if not dm_codes_result.get("success"):
                return dm_codes_result

            dm_info_result = await self.get_dm_info_by_codes(dm_codes_result["dm_codes"])
            if not dm_info_result.get("success"):
                return dm_info_result

            scanned = await consolidate_dm_by_article(dm_info_list=dm_info_result["dm_info"])
            result={
                "success": True,
                "container_id": container_id,
                "container_name": container_name_result["container_name"],
                "container_status": container_name_result.get("container_status"),
                "scanned": scanned
            }
            return result
        except Exception as e:
            logging.error(f"Error generating container kit: {e}")
            return {"success": False, "message": ERROR_GENERATE_CONTAINER_KIT}

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

