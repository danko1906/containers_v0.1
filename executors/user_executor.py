import bcrypt
import logging
from typing import Dict, Any
from message.engish_message import *


class UserExecutor:
    def __init__(self, db):
        self.db = db  # user_info

    async def get_user_info(self, login: str):
        query = "SELECT user_id, user_role FROM users WHERE login = %s"
        result = await self.db.fetch_one(query, (login,))
        return result  # {'id': 123, 'role': 'admin'}

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
            return bcrypt.checkpw(password.encode('utf-8'), password_hash)
        except Exception as e:
            logging.error(f"Error verifying user password: {e}")
            return False
