import discord
import configuration as cfg
import datetime
import pytz

from icecream import ic
from gspread.exceptions import WorksheetNotFound

from GlobalExceptions import ConfigurationErrorException
from TugasBot.Exceptions.CommandErrorException import CommandErrorException

from TugasBot.TugasBotInterface import TugasBotInterface
from Spreadsheet import DatabaseHelper as dbh, Parser
from Tugas import ListOfTugas

class TugasBot(TugasBotInterface):

  def __init__(self, 
    bot: discord.ClientUser = None, 
    message: discord.Message = None):
    self.bot = ""
    self.message = ""
    self.current_course = ""
    if bot: self.bot = bot
    if message: self.message = message
  
  def reset_messages(self):
    self.message = ''
    self.parsed_message = None

  def parse_message(self, message: str):
    # parse message from user
    self.parsed_message = Parser.parse_message(message)
    return self.parsed_message

  def set_message(self, message: discord.Message):
    self.message = message
    self.parse_message(message.content)
  
  def set_bot(self, bot):
    self.bot = bot

  def get_parsed_message(self):
    return list(self.parsed_message)

  def get_main_command(self):
    return self.get_parsed_message()[0]

  def is_message_ignorable(self, message: discord.Message):
    # ignoring message sent by the bot itself or another bot
    return (message.author == self.bot.user) or (message.author.bot)

  def default_response(self):
    # default response for undetected commands
    pass

  def request_spreadsheet(self):
    # return spreadsheet link
    return cfg.url_tugas

  def request_ujian(self):
    # return ujians
    return (
      "Currently unavailable.\n"
      "We'll be happy if you want to help us.\n"
      "Direct message me for further information."
    )

  def request_help(self):
    # return help
    helpfile = open(cfg.helpfile, 'r')
    try:
      response = helpfile.read()
    except IOError:
      response = "Error reading help file"
    finally:
      helpfile.close()

    return response

  #### TUGAS INTERFACES ####
  def request_tugas(self):
    # return tugases
    response = ""

    spreadsheet = dbh.getSpreadsheet(cfg.url_tugas)
    list_of_tugas = ListOfTugas.ListOfTugas()
    list_of_tugas = Parser.spreadsheetToTugases(spreadsheet)
    list_of_tugas.clean()
    list_of_tugas.sorted()
    list_of_tugas.getSpecific(self.parsed_message[1:])

    ### DISCORD SERVER ###
    if not isinstance(self.message.channel, discord.channel.DMChannel):

      # Get user role
      user_role = Parser.get_user_class_IF(self.message)
      if user_role:
        response += "User : {class_role}\n".format(class_role=user_role)
        list_of_tugas.descFilter(str(user_role))

    response += list_of_tugas.print_tugases()
    return response

  def add_tugas(self):
    # add tugas to tugas database
    try :
      data = Parser.extract_tugas(self.message.content.replace(f'{cfg.message_prefix}add', ""), cfg.url_tugas)
      retval = dbh.appendSpreadsheet(cfg.url_tugas, data)

      if retval:
        response = (
          "Task successfully added\n"
          "{course} - {title} - {deadline} - {url}".format(
            course = data["course"],
            title = data["title"],
            deadline = data["deadline"],
            url = data["spec_link"]
          )
        )
      else:
        response = "Something went wrong."

    except CommandErrorException as e:
      response = "[err : add] : " + str(e)
    
    return response.strip()


  ###### SCHEDULE INTERFACES ########
  def find_angkatan(self):
    '''
    Mendapatkan angkatan pada parsed message
    Mengembalikan string angkatan pertama yang ditemukan pada parsed message.
    Jika tidak ditemukan mengembalikan None
    '''
    for parsed_msg in self.get_parsed_message()[1:]:
      # if parsed message contains specific angkatan
      for angkatan in cfg.list_angkatan:
        if parsed_msg == str(angkatan):
          return angkatan
    return None
  

  def get_schedule(self, today: bool, angkatan: int):
    '''
    Mengambil schedule dalam bentuk schedule
    Jika today maka return schedule hari yang 'ini' saja
    Jika tidak maka return seluruh schedule
    '''
    # return schedule
    if cfg.schedule_sheet:
      spreadsheet = dbh.getSpreadsheet(cfg.url_tugas)
      sheet = None
      
      try:          
        sheet = spreadsheet.worksheet(cfg.schedule_sheet + str(angkatan))

        schedule = Parser.parse_schedule(sheet, today)
        return schedule

      except WorksheetNotFound:
        raise WorksheetNotFound("Schedule sheet not found.")

    else:
      raise ConfigurationErrorException("Schedule sheet not configured.")
  
  def print_schedule(self, schedule):
    compacted_schedule = Parser.compact_schedule(schedule)
    result = ""
    for day, daily_schedule in compacted_schedule.items():
      result += '**{day}**\n'.format(day=day)
      
      for hour, course in daily_schedule.items():
        curr_hour = hour.replace(" ", "").split(cfg.schedule_time_separator)
        result += '{hour_start} {separator} {hour_end} : {course}\n'.format(
          hour_start=curr_hour[0],
          hour_end=curr_hour[1],
          separator=cfg.schedule_time_separator,
          course=course
        )

      result += '\n'
        
    if result == "": return "Tidak ada jadwal."
    return result.strip('\n')

  def request_schedule(self):
    def is_present_requested():
      '''
      Mengembalikan true jika terdapat argumen '-p'
      false jika tidak
      '''
      for parsed_msg in self.get_parsed_message()[1:]:
        # if parsed message contains 'present' argument
        if parsed_msg == '-p':
          return True
      return False
    
    # return schedule
    try:
      today = is_present_requested()
      angkatan = self.find_angkatan()
      if angkatan is None:
        angkatan = cfg.default_angkatan

      schedule = self.get_schedule(today, angkatan)

      return self.print_schedule(schedule)

    except Exception as e:
      return "[err req_schedule] :" + e

  def set_current_course(self, course):
    self.current_course = course

  def get_current_course(self):
    return self.current_course

  def reminder_presensi(self):
    angkatan = cfg.default_angkatan
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    loc_now = utc_now.astimezone(pytz.timezone(cfg.tz))
    day_int_now = int(loc_now.strftime('%w'))
    hour_now = loc_now.strftime('%H.%M')

    try:
      schedule = self.get_schedule(True, angkatan)
      schedule = Parser.compact_schedule(schedule)

      for day, daily_schedule in schedule.items():
        if day_int_now == Parser.DAY_INT_DICT[day.lower()]:
          for hour, course in daily_schedule.items():
            start_hour, end_hour = hour.replace(" ", "").split(cfg.schedule_time_separator)

            # cek jam saat ini di antara jam di jadwal dan course beda sama sebelumnya
      
            if (
              course != self.get_current_course()
              and
              hour_now > start_hour 
              and 
              hour_now < end_hour 
            ) :
              ic(course, self.get_current_course())
              # set udah reminded untuk course yang sama
              self.set_current_course(course)

              return "**Presensi** : {course}".format(
                course = course
              )
            
      return None
    except Exception as e:
      return '[err : reminder_presensi] : ' + e

  def kerja(self):
    # main driver
    pass

  