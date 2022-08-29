## GLOBAL CONFIGURATION
author='jeremiaaxel#3677'
message_prefix = '$'
servicefile = ''
helpfile = 'help.txt'

# urls
url_ujian = ""
url_tugas = ""

# angkatan
list_angkatan = [19, 20]
default_angkatan = 19

# sheets
timeline_sheet = "timeline"
schedule_sheet = "schedule"
databases = ["dbmatkul"]

# time
tz = "Asia/Jakarta"
TIME_FORMAT = '%H:%M:%S'
working_hour = 11
schedule_time_separator = '-'

worksheet_exceptions = [timeline_sheet]
worksheet_exceptions.extend(databases)
for angkatan in list_angkatan:
  worksheet_exceptions.append(schedule_sheet + str(angkatan))

## REMINDER CONFIGURATION
guild_ids = []
channel_ids = []
reminder = True
scheduled_time = "07:00:00"
time_interval = 60 * 6 # in seconds

user_roles = []


exit_command = '$exit'

tubes_keywords = ['tugas besar', 'milestone']