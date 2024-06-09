import gspread
from gspread.utils import rowcol_to_a1
import datetime

gc = gspread.service_account(filename='credentials.json')

wks = gc.open("Solvrz_Leet").sheet1


def update_user_id(session_id):
    for i in range(100):
        cell_value = wks.cell(i+2, 1).value  # Adjust row index by 1
        if str(cell_value) == str(session_id):
            return
        else :
            if cell_value == None:
                cell_a1 = rowcol_to_a1(i+2, 1)  # Convert row and column to A1 notation
                wks.update(cell_a1, session_id)
                return
            else :
                continue

def update_email(email, session_id):
    current_datetime = datetime.datetime.now()
    for i in range(100):
        cell_value = wks.cell(i+2, 1).value  # Adjust row index by 1
        print(cell_value)
        if str(cell_value) == str(session_id):
            wks.update(f'E{i+2}', str(current_datetime))
            wks.update(f'C{i+2}', str(email))      # Update column C (index 3)
            return


def update_phone(phone, session_id):
    for i in range(100):
        cell_value = wks.cell(i+2, 1).value  # Adjust row index by 1
        if str(cell_value) == str(session_id):
            wks.update(f'D{i+2}', str(phone))      # Update column D (index 4)
            return

def update_msg(msg, session_id):
    for i in range(100):
        cell_value = wks.cell(i+2, 1).value  # Adjust row index by 1
        if str(cell_value) == str(session_id):
            wks.update(f'G{i+2}', str(msg))
            return

# wks.get('A2')
# print(wks.get('A2'))
#
# wks.update('A2', [[1,2], [4,5]])

# cell_value = wks.cell('A10').value
# cell_value = wks.cell(10, 1).value
# if cell_value is not None and cell_value != "":
#     print("Cell A2 has values:", cell_value)
# else:
#     print("Cell A2 is empty")


# import gspread
#
# gc = gspread.service_account(filename='credentials.json')
#
# wks = gc.open("Solvrz_Leet").sheet1
#
# # Define the range of columns you want to check (A1 to Dn)
# columns_to_check = ['A', 'B', 'C', 'D']
#
# # Get the maximum number of rows in the worksheet
# max_rows = wks.row_count
#
# # Loop through each row
# for row in range(1, max_rows + 1):
#     empty_cells = []
#
#     # Loop through each column
#     for col in columns_to_check:
#         cell_value = wks.cell(row, wks.find(col + '1').col).value
#         if not cell_value:
#             empty_cells.append(col + str(row))
#
#     # If there are empty cells in the row, update them
#     if empty_cells:
#         values_to_update = [[None] * len(columns_to_check) for _ in range(len(empty_cells))]
#         wks.update(empty_cells[0] + ':' + empty_cells[-1], values_to_update)