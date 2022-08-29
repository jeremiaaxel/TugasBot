import discord
import os
import queue
import time

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

bot = commands.Bot(message_prefix)
tugas_bot = TugasBot(bot)
inputQueue = queue.Queue()


def convert_to_time(scheduled_time, time_format):
    return datetime.strptime(scheduled_time, time_format).time()


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.event
async def on_message(message):
  # GUARDS
  if tugas_bot.is_message_ignorable(message): return
  if not message.content.startswith(message_prefix): return

  # get user interaction history
  print("[{t}]{author} : {content}".format(
    t=datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"),
    author=message.author,
    content=message.content))

  response = tugas_bot.set_message(message).process()
  await message.reply(response, mention_author=False)
  tugas_bot.reset_messages()

bot.run(os.getenv('TOKEN'))