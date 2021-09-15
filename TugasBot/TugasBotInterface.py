from TugasBot import ScheduleInterface, TugasInterface

# python ga perlu interface tapi maksudnya biar rapi aja sih
class TugasBotInterface():
  def is_message_ignoreable(self, message):
    # ignoring message sent by the bot itself
    pass

  def default_response(self):
    # default response for undetected commands
    pass

  def parse_message(self, message):
    # parse message from user
    pass

  def request_spreadsheet(self):
    # return spreadsheet link
    pass  

  def request_ujian(self):
    # return ujians
    pass

  def request_help(self):
    # return help
    pass
