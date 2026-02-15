import logging
from typing import List, Dict, Any
from message.engish_message import *


class DMExecutor:
    def __init__(self, db):
        self.db = db  # article_info



    # Функция для получения информации по нескольким DM-кодам
    async def get_dm_info_by_codes(self, dm_codes: List[str]) -> Dict[str, Any]:
        try:
            placeholders = ', '.join(['%s'] * len(dm_codes))
            query = f"""
                SELECT dm_without_tail, article, invoice_date, current_page_num
                FROM dm_info
                WHERE dm_without_tail IN ({placeholders})
            """
            rows = await self.db.fetch_all(query, tuple(dm_codes))
            result = [{"dm_without_tail": r[0], "article": r[1], "invoice_date": r[2], "current_page_num": r[3]} for r in rows]
            return {"success": True, "dm_info": result}
        except Exception as e:
            logging.error(f"Error fetching DM info: {e}")
            return {"success": False, "message": ERROR_FETCH_DM_CODES}

    # Новая функция для проверки наличия DM-кода в таблице
    async def check_dm_code_exists(self, dm_without_tail: str) -> Dict[str, Any]:
        try:
            query = """
                SELECT COUNT(*) FROM dm_info WHERE dm_without_tail = %s
            """
            count = await self.db.fetch_one(query, (dm_without_tail,))
            if count[0] == 0:
                return {"success": False, "message": DM_NOT_FOUND}
            return {"success": True, "message": f"DM code found: {count[0]} occurrences."}
        except Exception as e:
            logging.error(f"Error checking DM code existence: {e}")
            return {"success": False, "message": ERROR_FETCH_DM_INFO}
