import gspread
from configuration import servicefile

def getSpreadsheet(link: str):
  gc = gspread.service_account(filename=servicefile)
  return gc.open_by_url(link)

def appendSpreadsheet(link: str, data: dict):
  gc = gspread.service_account(filename=servicefile)
  spreadsheet = gc.open_by_url(link)
  worksheet = None
  for sheet in spreadsheet.worksheets():
    if sheet.title == data["course"]:
      worksheet = sheet
      break
    
  if worksheet is not None:
    print(list(data.values()))
    worksheet.append_row(list(data.values())[1:])
    return True

  return False
