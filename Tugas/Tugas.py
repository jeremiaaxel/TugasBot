import datetime
import pytz

from datetime import datetime as strToDate
from Helper.dates import HARI, BULAN

import configuration as cfg

tz = pytz.timezone(cfg.tz)

class Tugas:
  def __init__(self, course=None, name=None, deadline=None, spec_link=None, desc=[], other=None):
    '''
    course adalah mata kuliah
    name adalah nama tugas
    deadline adalah waktu tenggat tugas
    spec_link adalah link spesifikasi tugas
    desc adalah deskripsi
    other adalah link lain yang berhubungan dengan tugas
    '''
    if (course == None or course.isspace()):
      course = ""
    if (name == None or name.isspace()):
      name = ""
    if (deadline == None or deadline.isspace()):
      deadline = ""
    if (spec_link == None or spec_link.isspace()):
      spec_link = ""
    if (other == None or other == []):
      other = ""
    if (desc == None or desc == []):
      desc = ""
    else:
      tmp_desc = []
      for des in desc:
        tmp_desc.append(des.strip())
      del desc
      desc = tmp_desc
      
    self.__course = course
    self.__name = name
    self.__deadline = self.formatedDate2Date(deadline)
    self.__spec_link = spec_link
    self.__other = list(other)
    self.__desc = list(desc)

  def formatedDate2Date(self, date_in):
    time_in = None
    # if date_in is not empty
    if date_in != "":
      date_in = date_in.replace(',', '').split(' ')
    
      # if date_in is "DD/MM/YYYY HH.MM"
      if '/' in date_in[0]:
        if (len(date_in) > 1):
          time_in = date_in[1].split(".")
        date_in = date_in[0].split("/")

      # if date_in is "DD MMMM YYYY HH.MM"
      elif '/' not in date_in[0]:
        if (len(date_in) > 3):
          time_in = date_in[3].split(".")

        month = date_in[1]
        if month in BULAN:
          for i in range(len(BULAN)):
            if month == BULAN[i]:
              month = (i+1)
        date_in[1] = month
      
      if time_in is None:
        time_in = 23, 59

      date_in = strToDate(
        int(date_in[2]), int(date_in[1]), int(date_in[0]), int(time_in[0]), int(time_in[1]), tzinfo=tz)

    return date_in

  def __str__(self):
    return self.__name

  def setCourse(self, course):
    self.__course = course

  def getCourse(self):
    return self.__course
    
  def setName(self, name):
    self.__name = name
  
  def getName(self):
    return self.__name

  def setDeadline(self, deadline):
    self.__deadline = self.formatedDate2Date(deadline)
  
  def getDeadline(self):
    ic(self.__course, self.__name, self.__deadline)
    return self.__deadline

  def isEmpty(self):
    return len(self.__name) == 0

  def setSpecLink(self, spec_link):
    self.__spec_link = spec_link
  
  def getSpecLink(self):
    return self.__spec_link

  def setDesc(self, desc):
    self.__desc = desc

  def getDescription(self):
    return self.__desc

  def setOther(self, other):
    self.__other = other
  
  def getOther(self):
    return self.__other

  def getTimedelta(self):
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    now = utc_now.astimezone(pytz.timezone(cfg.tz))
    # now = strToDate.now() + datetime.timedelta(hours=7) # add 7 hours due to GMT+7 (in Western Indonesia Time)
    time_delta = self.__deadline - now
    time_delta -= datetime.timedelta(microseconds=time_delta.microseconds)
    return time_delta

  def describe(self):
    message = ""
    if self.getCourse() != "":
      message += "> *{course}*\n".format(course=self.__course)
    
    if self.getName() != "":
      message += "> **{name}**\n".format(name=self.__name)

    if (self.__deadline != ""):
      time_delta = self.getTimedelta()      
      message += "> Deadline: {day}, {deadline} ({time_left})\n".format(day=HARI[0 if self.__deadline.isoweekday() == 7 else self.__deadline.isoweekday()], deadline=self.__deadline.strftime('%d %B %Y %H:%M'), time_left=time_delta)
  
    if (self.__spec_link != ""):
      message += "> Specification: {spec_link}\n".format(spec_link=self.__spec_link)

    if (len(self.__desc) != 0) and self.__desc[0] != "":
      message += "> Description:\n"
      i = 0
      for item in self.__desc:
        message += "> {number}. {item}".format(number=i+1, item=item.strip()) + "\n"
        i += 1
      
    if (self.__other != ""):
      for (other_name, other_link) in self.__other:
        message += "> {other_name} : {other_link}\n".format(other_name=other_name, other_link=other_link)

    return message

  def describe_debug(self):
    print(self.describe())

  def extract_class_from_desc(self):  
    roles = [desc for desc in self.getDescription() if desc in cfg.user_roles]
    return roles