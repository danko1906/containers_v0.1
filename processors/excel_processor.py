import openpyxl
from openpyxl.utils import get_column_letter
import tempfile
from openpyxl.styles import Font, Border, Side, Alignment

class ExcelProcessor:
    @staticmethod
    async def create_excel_file(data):
        # Create a new Excel workbook and activate the worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        container_name=data['container_name']
        # Define styles
        times_new_roman_14 = Font(name='Times New Roman', size=14)  # Общий стиль шрифта
        bold_font = Font(name='Times New Roman', size=14, bold=True)  # Жирный стиль
        thin_border = Border(left=Side(style='thin'),
                             right=Side(style='thin'),
                             top=Side(style='thin'),
                             bottom=Side(style='thin'))  # Границы ячеек
        center_alignment = Alignment(horizontal='center', vertical='center')  # Выравнивание по центру

        # Set a standard column width
        for col in range(1, 20):  # На случай большого количества данных (1-20 колонок)
            column_letter = get_column_letter(col)
            ws.column_dimensions[column_letter].width = 50

        # Fill container information with bold text, custom font, and borders
        ws['A1'] = "Container"
        ws['A1'].font = bold_font
        ws['A1'].border = thin_border
        ws['A1'].alignment = center_alignment

        ws['B1'] = f"{data['container_name']}"
        ws['B1'].font = bold_font
        ws['B1'].border = thin_border
        ws['B1'].alignment = center_alignment

        # Initialize the start row and column
        row_start = 3
        col_start = 1

        # Write headers for each article and apply bold font, custom font, borders, and center alignment
        # Write headers for each article and apply bold font, custom font, borders, and center alignment
        for scanned_item in data.get('scanned', []):
            article = scanned_item['article']
            count = len(scanned_item['dms'])  # Подсчитываем количество dm_without_tail
            header_text = f"{article} ( {count} pcs )"
            column_letter = get_column_letter(col_start)

            ws[f"{column_letter}{row_start}"] = header_text
            ws[f"{column_letter}{row_start}"].font = bold_font
            ws[f"{column_letter}{row_start}"].border = thin_border
            ws[f"{column_letter}{row_start}"].alignment = center_alignment

            # Write all dm_without_tail values under the article with borders, font style, and center alignment
            row_dm = row_start + 1
            for dm in scanned_item['dms']:
                ws[f"{column_letter}{row_dm}"] = dm['dm_without_tail']
                ws[f"{column_letter}{row_dm}"].font = times_new_roman_14
                ws[f"{column_letter}{row_dm}"].border = thin_border
                ws[f"{column_letter}{row_dm}"].alignment = center_alignment
                row_dm += 1

            # Move to the next column for the next article
            col_start += 1


        # Save the Excel workbook to a temporary file
        file_name = f"{container_name}_kit"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx", prefix=file_name)
        wb.save(temp_file.name)

        return temp_file.name, temp_file.name.split("\\")[-1]  # Return file path and name