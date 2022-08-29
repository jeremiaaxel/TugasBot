import urllib.request
import re
import datetime
import pytz
import configuration as cfg

from .Tugas import Tugas

from icecream import ic
tz = pytz.timezone(cfg.tz)


class ListOfTugas:
  def __init__(self):
    self.__list_of_tugas = []
  
  def __len__(self):
    return len(self.__list_of_tugas)
    
  def append(self, tugas):
    self.__list_of_tugas.append(tugas)

  def extend(self, list_of_tugas):
    for tugas in list_of_tugas.getTugases():
      self.__list_of_tugas.append(tugas)

  def sorted(self) :
    self.__list_of_tugas = sorted(self.getTugases(), key=lambda x: x.getDeadline())

  def remove(self, tugas):
    try :
      self.__list_of_tugas.remove(tugas)
      return 1
    except (ValueError):
      return "No " + tugas + " in the list"

  def clean(self):
    count = 0
    for tugas in self.__getTugases():
      if tugas.isEmpty():
        count += 1
        self.__list_of_tugas.remove(tugas)
  
    return count
        
  def __getTugases(self):
    return self.__list_of_tugas
  
  def getTugases(self, present=None):
    if present:
      tugases = self.__list_of_tugas.copy()
      for tugas in self.__list_of_tugas:
        if tugas.getTimedelta() < datetime.timedelta(0):
          tugases.remove(tugas)
      return tugases
    else:
      return self.__getTugases()

  def getTugasesByInterval(self, days_interval):
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    time_now = utc_now.astimezone(tz)
    # time_now = datetime.datetime.now() + datetime.timedelta(hours=7)
    interval = datetime.datetime.timedelta(
      days=days_interval
    )
    tugases = self.__list_of_tugas.copy()
    for tugas in self.getTugases():
      if not (tugas.getDeadline() - time_now <= interval):
        tugases.remove(tugas)


  def print_tugases_debug(self) -> None:
    '''
    menerima list of tugas
    menampilkan list of tugas dalam format ke console/shell
    '''
    for item in self.getTugases():
      item.describe_debug()
      print()
    
    print("Count : {count}".format(count=len(self.getTugases())))

  def print_tugases(self) -> str:
    '''
    menerima list of tugas
    mengembalikan string list of tugas dalam format
    '''
    message = ""
    for item in self.getTugases():
      message += item.describe() + "\n"
    
    message += "Count: {count}".format(count=len(self.getTugases()))
    return message

  def tubesOnly(self):
    list_tubes = []
    for tugas in self.__list_of_tugas:
      for tubes_keyword in cfg.tubes_keywords:
        if tubes_keyword in tugas.getName().lower():
          list_tubes.append(tugas)
    return list_tubes

  def tubisOnly(self):
    list_tubis = [item for item in self.getTugases() if item not in self.tubesOnly()]
    return list_tubis


  def getSpecific(self, args):
    if "-B" in args or "-a" in args:
      for arg in args:
        if arg == "-B":
          self.__list_of_tugas = self.tubesOnly()
        elif arg == "-a":
          self.__list_of_tugas = self.__list_of_tugas
    else:
      self.__list_of_tugas = self.tubisOnly()

    if "-p" in args:
      self.__list_of_tugas = self.getTugases(True)

  def md_parser(self, url) -> None:
    '''
    menerima string url berisi teks
    mengappend list of tugas dengan tugas-tugas dari markdown
    '''
    file = urllib.request.urlopen(url)

    start = False

    course = None
    tugas_name, deadline, spec_link, desc, other = self.set_all_to_start()

    for line in file:
      decoded_line = line.decode("utf-8").replace("\n", "")

      if (decoded_line == "# Unfinished"):
        start = True

      if (decoded_line == "# Finished"):
        break

      # def __init__(self, course, name, deadline, spec_link, desc, other)
      if (start):

        if (re.search("^## ", decoded_line)):
          if (course != None and tugas_name != None):
            self.append(Tugas(course, tugas_name, deadline, spec_link, desc, other))

            # set kembali variable ke awal
            course = None
            tugas_name, deadline, spec_link, desc, other = self.set_all_to_start()

          course = decoded_line.replace("## ", "")
          
        # tugas_name
        elif (re.search("[0-9]+\. \[ \] ", decoded_line)):
          if (tugas_name != None):
            self.append(Tugas(course, tugas_name, deadline, spec_link, desc, other))

            # set kembali variabel ke awal, kecuali course
            tugas_name, deadline, spec_link, desc, other = self.set_all_to_start()
          tugas_name = decoded_line.split("] ")[1].replace(":", "")

        elif ("Deadline" in decoded_line):
          deadline = decoded_line.split("**Deadline :** ")[1]

        elif ("Spek" in decoded_line):
          spec_link = decoded_line.split("[Spek]")[1].replace("(", "").replace(")","")
        
        # other link
        elif (re.search("\[.+\]", decoded_line)):
          decoded_line = decoded_line.split("- [")[1].replace(")", "")
          other.append(decoded_line.split("]("))

        # description
        else:
          if (decoded_line != "" and (not "#" in decoded_line) and not decoded_line.isspace()):
            desc.append(decoded_line.replace("- ", ""))

  ### Fungsi lain
  def set_all_to_start(self):
    '''
    (tujuannya) 
    mengubah tugas_name = None, deadline = None, spec_link = None, desc = [], other = []
    '''
    return None, None, None, [], []

  def descFilter(self, user_role):
    list_tugas = self.__list_of_tugas.copy()
    for tugas in self.__list_of_tugas:
      if len(tugas.extract_class_from_desc()) > 0 and user_role not in tugas.extract_class_from_desc():
        list_tugas.remove(tugas)
     
    self.__list_of_tugas = list_tugas
    return list_tugas