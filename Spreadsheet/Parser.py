from Tugas import Tugas, ListOfTugas
from TugasBot.Exceptions.CommandErrorException import CommandErrorException
from Spreadsheet import DatabaseHelper as dbh
import configuration as cfg
from configuration import message_prefix, worksheet_exceptions, working_hour, schedule_time_separator

from icecream import ic
from datetime import datetime

import re

DATEREGEX = "((\d{1,2}(/|\s|-)\d{1,2}(/|\s|-)[\d]+)|(\d{1,2}(/|\s|-)((januari)|(februari)|(maret)|(april)|(mei)|(juni)|(juli)|(agustus)|(september)|(oktober)|(november)|(desember))(/|\s|-)\d{1,4}))"

COURSEREGEX = "([a-zA-Z]{2}\d{4})"

MONTH_INT_DICT = {
  "januari":1,
  "februari":2,
  "maret":3,
  "april":4,
  "mei":5,
  "juni":6,
  "juli":7,
  "agustus":8,
  "september":9,
  "oktober":10,
  "november":11,
  "desember":12
}

INT_MONTH_DICT = {
  1:"januari",
  2:"februari",
  3:"maret",
  4:"april",
  5:"mei",
  6:"juni",
  7:"juli",
  8:"agustus",
  9:"september",
  10:"oktober",
  11:"november",
  12:"desember"}

LINK = "https?"

DAY_INT_DICT = {
  'minggu':0,
  'senin':1,
  'selasa':2,
  'rabu':3,
  'kamis':4,
  'jumat':5,
  'sabtu':6,
}

def getCourses(spreadsheet):
  courses = COURSEREGEX
  for sheet in spreadsheet.worksheets():
    courses += "|(" + sheet.title + ")"
  return courses

def getTugas(course_sheet):
  print(course_sheet)

def parse_message(message):
  msg = message.replace(message_prefix, '', 1).split(' ')
  if len(msg) > 1:
    for ms in msg:
      if ms == "besar":
        ms = "-B"
      elif ms == "all":
        ms = "-a"
      elif ms == "present":
        ms = "-p"
  else:
    msg.append("None")

  return msg

def get_user_class_IF(message):
  for role in message.author.roles:
    if role.name in cfg.user_roles:
      return role.name

  return None

def parse_worksheet(sheet):
  '''
  Buat ngeparse tiap worksheet jadi tugas
  '''
  list_of_tugas = ListOfTugas.ListOfTugas()
  course = sheet.title
  
  for line in sheet.get_all_values():
    if (line[0] == "Title"):
      other_col = line[4:]
    else:
      title = line[0]
      deadline = line[1]
      spec = line[2]
      desc = [desc_i for desc_i in line[3].split(';') if len(desc_i) > 0 and not desc_i.isspace()]
      other = []
      for row in range(len(line[4:])):
        if line[4+row].strip():
          other.append([other_col[row],line[4+row]])

      tugas = Tugas.Tugas(course, title, deadline, spec, desc, other) 
      list_of_tugas.append(tugas)

  return list_of_tugas 

def spreadsheetToTugases(spreadsheet):
  '''
  Buat ngeparse spreadsheet, pembacaan tiap worksheet
  Hasilnya list of tugas
  '''
  list_of_tugas = ListOfTugas.ListOfTugas()
  for sheet in spreadsheet.worksheets():
    if sheet.title not in worksheet_exceptions:
      tugases = parse_worksheet(sheet)
      if tugases is not None:
        list_of_tugas.extend(tugases)

  return list_of_tugas

def parse_schedule(schedule_sheet, today:bool = False):
  current_day_int = int(datetime.today().strftime('%w'))
  schedule = {}
  values = schedule_sheet.get_all_values()

  for col in range(1, len(values[0])):
    if (values[0][col]):
      day = values[0][col]
      if ((today and DAY_INT_DICT[day.lower()] == current_day_int) or (not today)):
        day_dict = {}
        rows = [row for row in range(1, len(values)) if row <= working_hour]
        for row in rows:
          if (values[row][col] and re.search(COURSEREGEX, values[row][col])):
            hour = values[row][0]
            course = values[row][col] + " " + values[row][col+1]

            day_dict[hour] = course
            schedule[day] = day_dict

  return schedule

def compact_schedule(schedule):
  schedule_dict = {}
  for day, daily_schedule in schedule.items():
    day_dict = {}
    curr_hour = []
    curr_course = ""
    for hour, course in daily_schedule.items():
      if curr_course == course:
        curr_hour[1] = hour.replace(" ", "").split(schedule_time_separator)[1]
      else:
        if (curr_course != ""):
          compact_hour = '{hour_start} {separator} {hour_end}'.format(
            hour_start=curr_hour[0],
            hour_end=curr_hour[1],
            separator=schedule_time_separator,
          )

          day_dict[compact_hour] = curr_course

        curr_hour = hour.replace(" ", "").split(schedule_time_separator)
      curr_course = course

    compact_hour = '{hour_start} {separator} {hour_end}'.format(
      hour_start=curr_hour[0],
      hour_end=curr_hour[1],
      separator=schedule_time_separator,
    )

    day_dict[compact_hour] = curr_course

    schedule_dict[day] = day_dict
    
  return schedule_dict

def extract_tugas(message, url_tugas):
  course = None
  title = None
  spec_link = None
  deadline = None

  # course
  course = re.search(getCourses(dbh.getSpreadsheet(url_tugas)), message, re.IGNORECASE)

  # specification link
  for word in message.split(" "):
    if word.startswith(LINK):
      spec_link = word

  # deadline
  deadline = re.search(DATEREGEX, message, re.IGNORECASE)
  
  if None in (course, deadline):
    raise CommandErrorException(
      "Task failed. Please recheck your input\n" +
      "Tugas course, title, and deadline is required")
  else:
    course = course[0]
    deadline = deadline[0]
    print("Course :", course, "Title :", title, "Spec_link :", spec_link, "Deadline :", deadline)
    if spec_link is None:
      spec_link = ""

    title = message.replace(course, "").replace(deadline, "").replace(spec_link, "")

    title = title.replace("pada", "").strip()

    # other (?)
    deadline = convertDateToString( convertStringToDate( deadline ), "/", False)

    return {"course":course, "title":title, "deadline":deadline, "spec_link":spec_link}

def convertStringToDate(tanggal:str) -> list:
    converted = re.split("\s|/|-",tanggal)
    if (converted[1].isdigit()):
        converted[1] = int(converted[1])
    else:
        converted[1] = MONTH_INT_DICT[converted[1].lower()]
    return [int(converted[0]), converted[1] ,int(converted[2])]

def convertDateToString(date:list, delimiter:str, monthName:bool) -> str:
  return str(date[0]) +delimiter+ (INT_MONTH_DICT[date[1]].capitalize() if monthName else str(date[1])) +delimiter+ str(date[2])
