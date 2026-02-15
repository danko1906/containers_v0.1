import pandas as pd
from .excel_processor import ExcelProcessor
import re

class ShipmentProcessor:
    def __init__(self, query_executor):
        self.query_executor = query_executor

    async def parse_from_excel(self, file, folder_path):
        # Преобразуем файл в DataFrame
        excel_processor=ExcelProcessor()
        df = await excel_processor.read_excel(file)

        if df is None:
            return {}

        wholesaler_long_name = df.iloc[16, 7]
        match = re.match(r'^(.*?)(?=, ИНН)', wholesaler_long_name)

        if match:
            wholesaler_name = match.group(1)

        wholesaler_id = await self.query_executor.add_wholesaler(wholesaler_name=wholesaler_name)
        holder_long_name = df.iloc[13, 7]
        match = re.match(r'^(.*?)(?=, ИНН)', holder_long_name)
        if match:
            holder_name = match.group(1)

        holder_id = await self.query_executor.add_wholesaler(wholesaler_name=holder_name)
        date_str = df.iloc[9, 1]
        date = excel_processor.parse_date(date_str)
        order_number=excel_processor.format_invoice_data(invoice_str=date_str, seller_id=holder_id, consumer_id=wholesaler_id)
        isError,error_text=await self.query_executor.check_existing_order(order_number=order_number)
        if isError:
            result={}
        else:
            shipments = await self._parse_shipments(df)  # Асинхронная обработка
            result={
                "holder_id": holder_id[0],
                "wholesaler_id": wholesaler_id[0],
                "date": date,
                "shipments": shipments,
                "isFBO": False
            }
        return isError, error_text, result, order_number


    async def _parse_shipments(self, df):
        shipments = []
        article_row = 22

        while True:
            article = df.iloc[article_row, 3]
            if pd.isna(article):
                break

            gtin = await self.query_executor.get_gtin_by_article(article)  # Асинхронный запрос
            amount = df.iloc[article_row, 40]

            shipments.append({
                "article": article,
                "gtin": gtin,
                "amount": amount,
                "remain": amount,
                "scanned_dm": []
            })

            article_row += 1

        return shipments