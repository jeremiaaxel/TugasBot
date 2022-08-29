import discord
import os
from datetime import datetime
from pytz import timezone
from discord.ext import commands, tasks

# custom library
from Tugas import ListOfTugas, Parser
from Spreadsheet import DatabaseHelper as dbh

# configuration
import configuration as cfg

## GLOBAL CONFIGURATION
tz = timezone(cfg.tz) # di ListOfTugas juga ada configuration
url_ujian = cfg.url_ujian
url_tugas = cfg.url_tugas
message_prefix = cfg.message_prefix
TIME_FORMAT = cfg.TIME_FORMAT

## REMINDER CONFIGURATION
target_channel_id = cfg.target_channel_id
reminder = cfg.reminder
scheduled_time = cfg.scheduled_time

bot = commands.Bot(message_prefix)

def convert_to_time(scheduled_time, time_format):
  return datetime.strptime(scheduled_time, time_format).time()

@bot.event
async def on_ready():
  print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
  
  # To ignore self chat
  if message.author == bot.user:
    return
  if message.author.bot: 
    return

  # message starts with message_prefix
  if message.content.startswith(message_prefix):
    # get user interaction history
    print("[{t}]{author} : {content}".format(
      t=datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"), author=message.author, 
      content=message.content
    ))

    # initialization
    msg = Parser.parse_message(message.content.replace(message_prefix, "")) # parse message content
    print(msg)
    response = "" # initialize response

    # REQUEST spreadsheet
    if msg[0] == f'spreadsheet':
      response += url_tugas
    
    # REQUEST tugas
    elif msg[0] == f'tugas'\
      or msg[0] == f'guessilldie':     

      ##################### DISCORD SERVER #####################
      if not isinstance(message.channel, discord.channel.DMChannel):

        # Get user role
        user_role = Parser.get_user_class_IF(message)
        if user_role != -1:
          response += "User : IF K{class_no}".format(class_no=str(user_role))
      #################### END DISCORD SERVER ######################

      spreadsheet = dbh.getSpreadsheet(url_tugas)
      list_of_tugas = ListOfTugas.ListOfTugas()
      list_of_tugas = Parser.spreadsheetToTugases(spreadsheet)
      list_of_tugas.sorted()
      list_of_tugas.getSpecific(msg[1:])
      response += list_of_tugas.print_tugases()
      
    # REQUEST add tugas
    elif msg[0] == f'add':
      await message.reply("This is beta feature", mention_author=False)
      try :
        data = Parser.extract_tugas(message.content.replace(f'{message_prefix}add', ""), url_tugas)
        retval = dbh.appendSpreadsheet(url_tugas, data)
        if retval:
          response += (
            "Task successfully added\n"
            "{course} - {title} - {deadline} - {url}".format(
              course = data["course"],
              title = data["title"],
              deadline = data["deadline"],
              url = data["spec_link"]
            )
          )
      except Exception as e:
        print(e)
        response += str(e)

    # REQUEST ujian
    elif msg[0] == f'ujian':
      response += (
        "Currently unavailable.\n"
        "We'll be happy if you want to help us.\n"
        "Direct message me for further information."
      )

    # REQUEST help
    elif msg[0] == f'help':
      response += (
        "Commands :\n"
        " `$tugas [options]` untuk melihat tugas(terurut berdasarkan deadline terdekat)\n"
        " `$guessilldie`     meninggoy\n"
        " `$spreadsheet`     melihat link google spreadsheet\n"
        " `$help`            melihat tulisan ini\n"
        "\n"
        "Options :\n"
        "     -a, all        melihat seluruh tugas\n"
        "     -B, besar      melihat tugas besar\n"
        "     -p, present    melihat tugas tanpa yang lampau\n"
        "     <no option>    melihat tugas biasa\n"
      )

    # bot configuration
    elif msg[0] == f'bot':
      if message.channel.id == target_channel_id:
        global reminder # THESE ARE BAD
        global scheduled_time

        if len(msg) > 2:
          if msg[1] == 'reminder':
            if msg[2] == 'off':
              reminder = False
              response += "Reminder off"
            elif msg[2] == 'on':
              reminder = True
              response += "Reminder on at {}".format(scheduled_time)
            elif msg[2] == 'change' and msg[3] is not None:
              scheduled_time = msg[3]
              try:
                convert_to_time(scheduled_time, TIME_FORMAT)
                response += "reminder time changed to {}".format(scheduled_time)
              except ValueError:
                response += "time format error {}".format(TIME_FORMAT)
            elif msg[2] == 'status':
              response += "reminder : {active}\ntime : {scheduled_time}".format(active = "on" if reminder else "off", scheduled_time = scheduled_time)
            
          
        if response == "":
          response += "Command not recognized"

      else:
        response += "response not available for this channel"

    else:
      response += "Error"

    await message.reply(response, mention_author=False)
            
  # message is not started with message_prefix  
  else:
    # only response if message is in DM
    if isinstance(message.channel, discord.channel.DMChannel):
      if message.content.startswith('Contribute'):
        txt = (
          "If you want to contribute to this bot, feel free to contact jeremiaaxel#3677.\n"
          "We're glad to have you.\n"
          "Thank you!"
        )

      else:
        txt = (
          "Hello. Anything I can help you with?\n"
          "`Contribute` if you want to contribute to this bot."
        )

      await message.channel.send(txt)

### LOOPING SEND MESSAGE ###
def is_the_time():
  time_object = convert_to_time(scheduled_time, TIME_FORMAT)
  return datetime.now(tz).time().hour == time_object.hour and datetime.now(tz).time().minute == time_object.minute

# bug, gimana caranya biar dia ngirim cuma sekali sehari
# dan bisa dinyalain/dimatiin
@tasks.loop(seconds=55)
async def called_once_a_day():
  if reminder and is_the_time():
    message_channel = bot.get_channel(target_channel_id)

    spreadsheet = dbh.getSpreadsheet(url_tugas)
    tugas = Parser.parse_worksheet(spreadsheet.worksheet("Timeline"))
    tugas.getTugasesByInterval(3)
    response = tugas.print_tugases()
    
    await message_channel.send(response)

@called_once_a_day.before_loop
async def before():
    await bot.wait_until_ready()
    print("Loop bot ready")

called_once_a_day.start()
bot.run(os.getenv('TOKEN'))
    
# client.run(os.getenv('TOKEN'))