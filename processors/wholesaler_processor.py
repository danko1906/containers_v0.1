import os
from .excel_processor import ExcelProcessor
import asyncio

class WholesalerProcessor:
    def __init__(self, query_executor):
        self.query_executor = query_executor

    async def extract_data(self, folder_path):
        wholesalers = []
        files = [f for f in os.listdir(folder_path) if f.endswith('.xlsx')]

        tasks = []
        for file in files:
            file_path = os.path.join(folder_path, file)
            tasks.append(self._process_file(file_path, file, wholesalers))

        await asyncio.gather(*tasks)
        return wholesalers

    async def _process_file(self, file_path, file, wholesalers):
        df = await ExcelProcessor.read_excel(file_path)
        if df is not None:
            await self._process_wholesaler(df, file, wholesalers)

    async def _process_wholesaler(self, df, file, wholesalers):
        wholesaler_name = df.iloc[5, 7]
        wholesaler_id = await self.query_executor.get_wholesaler_id(wholesaler_name)

        # Если метод get_wholesaler_id является синхронным, его можно оставить так
        # или сделать асинхронным, если база данных поддерживает асинхронные запросы.
        wholesaler_id = wholesaler_id[0]

        date_str = df.iloc[1, 1]
        date = ExcelProcessor.parse_date(date_str)

        existing = next((w for w in wholesalers if w["id"] == wholesaler_id), None)

        if existing:
            existing['files'][date] = file
        else:
            wholesalers.append({
                "id": wholesaler_id,
                "name": wholesaler_name,
                "files": {date: file}
            })