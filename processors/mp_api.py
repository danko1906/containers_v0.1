import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import aiohttp
from processors.query_executor import QueryExecutor

# Helper to format the date
def format_date(input_date: str) -> str:
    date_obj = datetime.strptime(input_date, "%Y-%m-%dT%H:%M:%SZ")
    return date_obj.strftime("%d.%m.%Y")

# Class to load API configurations
class ApiConfigLoader:
    def __init__(self, env_file=".env"):
        load_dotenv(env_file)
        self.ozon_accounts = self._load_accounts(prefix="OZON")

    def _load_accounts(self, prefix):
        accounts = []
        index = 1
        while True:
            api_key = os.getenv(f"{prefix}_API_KEY_{index}")
            client_id = os.getenv(f"{prefix}_CLIENT_ID_{index}")
            account_name = os.getenv(f"{prefix}_ACCOUNT_NAME_{index}")
            wholesaler_name = os.getenv(f"{prefix}_WHOLESALER_NAME_{index}")
            wholesaler_id = os.getenv(f"{prefix}_WHOLESALER_ID_{index}")
            if not api_key or not client_id or not account_name:
                break
            accounts.append({
                "client_id": client_id,
                "api_key": api_key,
                "account_name": account_name,
                "wholesaler_name": wholesaler_name,
                "wholesaler_id": wholesaler_id
            })
            index += 1
        return accounts

    def get_accounts(self):
        return self.ozon_accounts

    def find_account_by_wholesaler_id(self, wholesaler_id):
        for account in self.ozon_accounts:
            if account["wholesaler_id"] == wholesaler_id:
                return account
        return None

# Base API class for Ozon API integration
class ApiBase:
    def __init__(self, api_key):
        self.headers = {}

# Main class for interacting with the Ozon API
class OzonAPI(ApiBase):
    def __init__(self, client_id, api_key, base_url, wholesaler_name, wholesaler_id):
        super().__init__(api_key=api_key)
        self.base_url = base_url
        self.wholesaler_name = wholesaler_name
        self.wholesaler_id = wholesaler_id
        self.headers.update({
            "Client-Id": client_id,
            "Api-Key": api_key,
        })

# Class to fetch supply orders and details
class OzonAPIWithSupplyOrders(OzonAPI):
    async def fetch_supply_orders(self, states=None, limit=100):
        """Получает список заявок на поставку из Ozon API."""
        url = f"{self.base_url}/v2/supply-order/list"

        # Если статусы не переданы, используем дефолтный
        if states is None:
            states = ["ORDER_STATE_DATA_FILLING", "ORDER_STATE_READY_TO_SUPPLY"]

        payload = {
            "filter": {"states": states},
            "paging": {"from_supply_order_id": 0, "limit": limit},
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=self.headers, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()

                    # Проверяем, есть ли в ответе список заявок
                    return data.get("supply_order_id", [])  # Предположительно правильное поле
            except aiohttp.ClientResponseError as e:
                print(f"Ошибка запроса к Ozon API: {e.status} - {e.message}")
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")

    async def get_supply_order_details(self, supply_order_ids):
        url = f"{self.base_url}/v2/supply-order/get"
        payload = {"order_ids": supply_order_ids}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                response.raise_for_status()
                return await response.json()

    async def fetch_bundle_details(self, bundle_ids, is_asc=True, limit=100, query=None, sort_field="UNSPECIFIED", last_id=None):
        url = f"{self.base_url}/v1/supply-order/bundle"
        payload = {
            "bundle_ids": bundle_ids,
            "is_asc": is_asc,
            "limit": limit,
            "query": query,
            "sort_field": sort_field,
            "last_id": last_id,
        }
        payload = {key: value for key, value in payload.items() if value is not None}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                response.raise_for_status()
                return await response.json()

# OrderProcessor to handle business logic
class OrderProcessor:
    def __init__(self, wholesaler_id, wholesaler_name):
        self.wholesaler_id = wholesaler_id
        self.wholesaler_name = wholesaler_name

    async def validate_bundle_id(self, bundle_id, query_executor: QueryExecutor):
        config_loader = ApiConfigLoader()
        account = config_loader.find_account_by_wholesaler_id(wholesaler_id=self.wholesaler_id)

        if not account:
            print("Не удалось загрузить учетные записи Ozon.")
            return None

        ozon_api = OzonAPIWithSupplyOrders(
            client_id=account["client_id"],
            api_key=account["api_key"],
            base_url="https://api-seller.ozon.ru",
            wholesaler_name=account["wholesaler_name"],
            wholesaler_id=account["wholesaler_id"]
        )
        bundle_detail = await ozon_api.fetch_bundle_details(bundle_ids=[bundle_id])

        filtered_items = [item for item in bundle_detail['items'] if await query_executor.is_gtin_in_sku_info(gtin=f"0{item['barcode']}")]
        return {
            'items': filtered_items,
            'total_count': len(filtered_items),
            'last_id': filtered_items[-1]['sku'] if filtered_items else None,
            'has_next': bundle_detail['has_next']
        }

    async def filter_data_by_validation(self, supplier_data, query_executor: QueryExecutor):
        supplies_to_remove = []
        for date, supply_data in supplier_data["supplies"].items():
            valid_supplies = []
            for shipment in supply_data["one_day_supplies"]:
                for shipment_number, bundle_id in shipment.items():
                    if await self.validate_bundle_id(bundle_id=bundle_id, query_executor=query_executor):
                        valid_supplies.append(shipment)
                    break
            if valid_supplies:
                supply_data["one_day_supplies"] = valid_supplies
            else:
                supplies_to_remove.append(date)

        for date in supplies_to_remove:
            del supplier_data["supplies"][date]

        if not supplier_data["supplies"]:
            return None

        return supplier_data

    @staticmethod
    def filter_orders_by_deadline(supply_data):
        today = datetime.utcnow()
        deadline_threshold = today + timedelta(days=7)

        filtered_orders = []
        for order in supply_data.get('orders', []):
            timeslot_out = order.get("timeslot", {})
            timeslot_value = timeslot_out.get("value", {})
            timeslot_in = timeslot_value.get("timeslot", {})
            timeslot_from = timeslot_in.get('from')

            if timeslot_from:
                timeslot_from_dt = datetime.fromisoformat(timeslot_from.replace('Z', ''))
                if timeslot_from_dt <= deadline_threshold:
                    filtered_orders.append(order)

        return {"orders": filtered_orders}

    @staticmethod
    def transform_orders_data(data):
        result = {}
        orders = data.get('orders', [])
        for order in orders:
            supply_order_number = order.get('supply_order_number')
            timeslot_out=order.get("timeslot")
            timeslot_value=timeslot_out.get("value")
            timeslot_in=timeslot_value.get("timeslot")
            timeslot_from = timeslot_in.get('from')
            supplies = order.get('supplies', [])
            bundle_id = supplies[0].get ('bundle_id') if supplies else None
            if supply_order_number:
                formatted_date = format_date(input_date=timeslot_from)
                result[supply_order_number] = {'date': formatted_date, 'bundle_id': bundle_id}
        return result

    @staticmethod
    def consolidated_by_date(data):
        transformed = {}
        for supply_order_number, details in data.items():
            date = details["date"]
            bundle_id = details["bundle_id"]
            if date not in transformed:
                transformed[date] = {"one_day_supplies": []}
            transformed[date]["one_day_supplies"].append({supply_order_number: {"bundle_id": f"{bundle_id}", "status": "new"}})
        return transformed


    async def available_by_date(self, supply_data):
        filtered_orders = self.filter_orders_by_deadline(supply_data)
        transformed_data = self.transform_orders_data(data=filtered_orders)
        consolidated_by_date = self.consolidated_by_date(data=transformed_data)
        result = {
            "id": f"{self.wholesaler_id}",
            "name": f"{self.wholesaler_name}",
            "supplies": consolidated_by_date
        }
        return result

    @staticmethod
    async def extract_offer_id_gtin_quantity(data, query_executor: QueryExecutor):
        shipments = []
        for item in data.get("items", []):
            offer_id = item["offer_id"]
            barcode = item["barcode"]
            quantity = item["quantity"]
            gtin=await query_executor.get_gtin_by_article(article=offer_id)
            shipments.append({
                "article": offer_id,
                "gtin": gtin,
                "amount": quantity,
                "remain": quantity,
                "scanned_dm": []
            })
        return shipments

    async def create_shipment_data(self, date, ship_list, shipment_number, query_executor: QueryExecutor):
        transformed_ship_list = await self.extract_offer_id_gtin_quantity(data=ship_list,query_executor=query_executor)
        return {
            "wholesaler_id": self.wholesaler_id,
            "wholesaler_name": self.wholesaler_name,
            "shipment_number":shipment_number,
            "date": date,
            "shipments": transformed_ship_list,
            "isFBO": True
        }

# Fetch orders by bundle_id asynchronously
async def get_orders_by_bundles(bundle_ids, wholesaler_id, date, shipment_number,query_executor: QueryExecutor):
    config_loader = ApiConfigLoader()
    account = config_loader.find_account_by_wholesaler_id(wholesaler_id=wholesaler_id)

    if not account:
        print("Не удалось загрузить учетные записи Ozon.")
        return

    ozon_api = OzonAPIWithSupplyOrders(
        client_id=account["client_id"],
        api_key=account["api_key"],
        base_url="https://api-seller.ozon.ru",
        wholesaler_name=account["wholesaler_name"],
        wholesaler_id=account["wholesaler_id"]
    )
    non_filtered_by_date = await ozon_api.fetch_bundle_details(bundle_ids=bundle_ids)
    order = OrderProcessor(wholesaler_id=account["wholesaler_id"], wholesaler_name=account["wholesaler_name"])
    orders_dict = await order.create_shipment_data(date=date, ship_list=non_filtered_by_date, shipment_number=shipment_number,query_executor=query_executor)
    return orders_dict

# Fetch FBO supplies asynchronously
async def get_fbo_supplies(query_executor: QueryExecutor):
    config_loader = ApiConfigLoader()
    accounts = config_loader.get_accounts()

    if not accounts:
        print("Не удалось загрузить учетные записи Ozon.")
        return

    consolidated_list = []
    for account in accounts:
        ozon_api = OzonAPIWithSupplyOrders(
            client_id=account["client_id"],
            api_key=account["api_key"],
            base_url="https://api-seller.ozon.ru",
            wholesaler_name=account["wholesaler_name"],
            wholesaler_id=account["wholesaler_id"]
        )

        try:
            supply_order_ids = await ozon_api.fetch_supply_orders()
            if not supply_order_ids:
                print("Нет доступных заявок на поставку.")
                return

            supply_orders = await ozon_api.get_supply_order_details(supply_order_ids)
            order = OrderProcessor(wholesaler_id=account["wholesaler_id"], wholesaler_name=account["wholesaler_name"])
            consolidated = await order.available_by_date(supply_data=supply_orders)
            #filtered_by_gtin = await order.filter_data_by_validation(supplier_data=consolidated, query_executor=query_executor)
            consolidated_list.append(consolidated)

        except aiohttp.ClientError as e:
            print(f"Ошибка при работе с API: {e}")

    return consolidated_list

# Main execution

