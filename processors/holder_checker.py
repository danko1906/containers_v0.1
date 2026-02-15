import asyncio


class HolderChecker:
    def __init__(self, query_executor):
        self.query_executor = query_executor

    async def _process_error(self, shipment, dm_code, shipments_with_error):
        # Получаем DM без хвостовой части
        dm_without_tail = dm_code[:31]
        # Запрашиваем информацию о холдере по укороченному DM
        holder_result = await self.query_executor.get_holder_info(dm_without_tail)
        if holder_result:
            error_detail = {
                "real_holder_id": holder_result[0],
                "real_holder_name": holder_result[1],
                "invoice_date": holder_result[2],
                "current_page_num": holder_result[3],
                "article": holder_result[4],
                "gtin": holder_result[5],
                "error_dm": dm_without_tail,
            }
            shipments_with_error["total"] += 1
            shipments_with_error["error_dm_list"].append(error_detail)
        return shipments_with_error

    async def check(self, dict_data, file_name):
        error_data = {}
        success_data = {}
        shipments_with_error = {"total": 0, "error_dm_list": []}

        original_data = dict_data.copy()


        # Получаем данные заказа, включая уже сохраненные отправления
        existing_order = await self.query_executor.get_order_details(file_name)
        existing_shipments = set()
        order_holder_id =existing_order.get("holder_id")

        if existing_order:
            for shipment in existing_order.get("shipments", []):
                for scanned_dm in shipment.get("scanned_dm", []):
                    existing_shipments.add(next(iter(scanned_dm)))

        for shipment in dict_data["shipments"]:
            valid_dm = []

            for scanned_dm in shipment["scanned_dm"]:
                dm_code = next(iter(scanned_dm))

                # Пропускаем проверку, если DM уже сохранен
                if dm_code in existing_shipments:
                    valid_dm.append(scanned_dm)
                    continue

                dm_without_tail = dm_code[:31]
                holder_result = await self.query_executor.get_holder_info(dm_without_tail)

                if holder_result:
                    isFBO = scanned_dm[dm_code].get("isFBO", False)
                    scanned_holder_id = int(scanned_dm[dm_code].get("holder_id"))


                    if (isFBO and holder_result[0] == scanned_holder_id) or holder_result[0] == order_holder_id:
                        valid_dm.append(scanned_dm)
                    else:
                        shipments_with_error = await self._process_error(shipment, dm_code, shipments_with_error)

            shipment["scanned_dm"] = valid_dm  # Обновляем список корректных DM-кодов

        if shipments_with_error["total"] > 0:
            error_data[file_name] = shipments_with_error

        success_data[file_name] = original_data  # Возвращаем исходную структуру данных

        return success_data, error_data
