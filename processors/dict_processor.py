from collections import defaultdict

async def consolidate_dm_by_article(dm_info_list: list) -> list:
    # Создаем словарь, где ключ - article, а значение - список соответствующих dms
    consolidated_data = defaultdict(list)

    # Группируем dm по article
    for dm_info in dm_info_list:
        article = dm_info["article"]
        consolidated_data[article].append({
            "dm_without_tail": dm_info["dm_without_tail"],
            "invoice_date": dm_info["invoice_date"],
            "current_page_num": dm_info["current_page_num"]
        })

    # Преобразуем результат в список словарей, добавляя total для каждого article
    result = [
        {
            "article": article,
            "dms": dms,
            "total": len(dms)  # Количество dms для каждого article
        }
        for article, dms in sorted(consolidated_data.items())  # Сортируем по article
    ]

    return result



async def html_escape(text):
    # Словарь с заменами
    replacements = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&apos;": "'"
    }

    # Проходим по каждому символу и заменяем
    for entity, symbol in replacements.items():
        text = text.replace(symbol, entity)

    return text

async def html_unescape(text):
    # Словарь с заменами
    replacements = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&apos;": "'"
    }

    # Проходим по каждому символу и заменяем
    for entity, symbol in replacements.items():
        text = text.replace(entity, symbol)

    return text