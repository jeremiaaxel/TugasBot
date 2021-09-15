import discord
import os
import queue

from icecream import ic

from datetime import datetime
from pytz import timezone
from discord.ext import commands, tasks

# configuration
import configuration as cfg
from TugasBot.TugasBot import TugasBot

## GLOBAL CONFIGURATION
tz = timezone(cfg.tz)  # di ListOfTugas juga ada configuration
url_ujian = cfg.url_ujian
url_tugas = cfg.url_tugas
message_prefix = cfg.message_prefix
TIME_FORMAT = cfg.TIME_FORMAT

## REMINDER CONFIGURATION
guild_ids = cfg.guild_ids
target_channel_ids = cfg.channel_ids
reminder = cfg.reminder
scheduled_time = cfg.scheduled_time
time_interval = cfg.time_interval

bot = commands.Bot(message_prefix)
tugas_bot = TugasBot(bot)
inputQueue = queue.Queue()

def convert_to_time(scheduled_time, time_format):
	return datetime.strptime(scheduled_time, time_format).time()


@bot.event
async def on_ready():
  print(f'We have logged in as {bot.user}')
  
  # cmd = input("> ")
  # if cmd == 'in':
  #   await send_channel_entry()

@bot.event
async def on_message(message):
	if tugas_bot.is_message_ignorable(message):
		return

	# message starts with message_prefix
	if message.content.startswith(message_prefix):
		# get user interaction history
		print("[{t}]{author} : {content}".format(
		    t=datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"),
		    author=message.author,
		    content=message.content))

		tugas_bot.set_message(message)

		response = None

		if tugas_bot.get_main_command() == f'test':
			response = tugas_bot.reminder_presensi()

		# REQUEST spreadsheet
		elif tugas_bot.get_main_command() == f'sheet':
			response = tugas_bot.request_spreadsheet()

		# REQUEST tugas
		elif tugas_bot.get_main_command() == f'tugas'\
          or tugas_bot.get_main_command() == f'guessilldie':
			response = tugas_bot.request_tugas()

		# REQUEST add tugas
		elif tugas_bot.get_main_command() == f'add':
			await message.reply("This feature is currently in development.",
			                    mention_author=False)
			response = tugas_bot.add_tugas()

		# REQUEST ujian
		elif tugas_bot.get_main_command() == f'ujian':
			response = tugas_bot.request_ujian()

		# REQUEST help
		elif tugas_bot.get_main_command() == f'help':
			response = tugas_bot.request_help()

		# REQUEST schedule
		elif tugas_bot.get_main_command() == f'schedule':
			response = tugas_bot.request_schedule()

		# bot configuration
		# belum di-reformat
		elif tugas_bot.get_main_command() == f'bot':
			if message.channel.id in target_channel_ids:

				# THESE ARE BAD
				global reminder
				global scheduled_time

				if len(tugas_bot.get_parsed_message()) > 2:
					if tugas_bot.get_parsed_message()[1] == 'reminder':
						if tugas_bot.get_parsed_message()[2] == 'off':
							reminder = False
							response = "Reminder off"
						elif tugas_bot.get_parsed_message()[2] == 'on':
							reminder = True
							response = "Reminder on"
						elif tugas_bot.get_parsed_message(
						)[2] == 'change' and tugas_bot.get_parsed_message(
						)[3] is not None:
							scheduled_time = tugas_bot.get_parsed_message()[3]
							try:
								convert_to_time(scheduled_time, TIME_FORMAT)
								response = "reminder time changed to {}".format(
								    scheduled_time)
							except ValueError:
								response = "time format error {}".format(
								    TIME_FORMAT)
						elif tugas_bot.get_parsed_message()[2] == 'status':
							response = "reminder : {active}\ntime : {scheduled_time}".format(
							    active="on" if reminder else "off",
							    scheduled_time=scheduled_time)

				if response is None:
					response = "Command not recognized"

			else:
				response = "response not available for this channel"


		else:
			response = "Command not recognized"

		await message.reply(response, mention_author=False)
		tugas_bot.reset_messages()

	# message is not started with message_prefix
	else:
		# only response if message is in DM
		if isinstance(message.channel, discord.channel.DMChannel):
			if message.content.lower().startswith('Contribute'):
				txt = (
				    "If you want to contribute to this bot, feel free to contact {author}.\n"
				    "We're glad to have you.\n"
				    "Thank you!".format(author=cfg.author))

			else:
				txt = ("Hello. Anything I can help you with?\n"
				       "`Contribute` if you want to contribute to this bot.")

			await message.channel.send(txt)


### LOOPING SEND MESSAGE ###
@tasks.loop(seconds=time_interval)
async def called_once_per_interval():
	if reminder:
		response = tugas_bot.reminder_presensi()
		if response:
			for target_channel_id in target_channel_ids:
				message_channel = bot.get_channel(target_channel_id)

				print('[{t}] {reminder}'.format(
				    t=datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"),
				    reminder=response))
				await message_channel.send(response)


@called_once_per_interval.before_loop
async def before():
	await bot.wait_until_ready()
	print("Loop bot ready")


def send_channel_entry(inputQueue):
  def req_input():
    print("Message ? 'exit' to close message input")
    msg = input("> ")
    return msg

  channels_id = cfg.channel_ids
  selected_channel = None
  channels = []

  for channel_id in channels_id:
    channel = bot.get_channel(channel_id)
    channels.append(channel)

  for i in range(len(channels)):
    print("[{channel_no}] : {channel_name}".format(
      channel_no = i,
      channel_name = channels[i].name
    ))

  idx = int(input("Channel no : "))
  selected_channel = channels[idx]
    
  if selected_channel:
    print("Connected to {channel}".format(
      channel = channel.name)
    )

    msg = req_input()
    while (msg != cfg.exit_command):
      inputQueue.put([channel, msg])
      msg = req_input()

    inputQueue.put([channel, msg])


# inputThread = threading.Thread(
#   target=send_channel_entry, 
#   args=(inputQueue,), 
#   daemon=True
# )
# inputThread.start()

# while (True):
#   if (inputQueue.qsize() > 0):
#     channel, message = inputQueue.get()
#     print("{channel} << {message}".format(channel=channel.name, message=message))
#     # channel.send(message)

#     if message == cfg.exit_command:
#       print("Exiting")
#       break

#   time.sleep(0.01) 

called_once_per_interval.start()

bot.run(os.getenv('TOKEN'))
