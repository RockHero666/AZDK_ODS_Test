import datetime
from telebot import TeleBot

class logger:

    def __init__(self, filename = None,file_log = None):

        self.telebot = TeleBot("5811298447:AAF0--61uBVvKgFvMeYs76fB1QjmhaihU-Y", -822387173)
        self.new_file = False

        if not filename:
            self.filename_update()

        if not file_log:
            self.file = open(self.filename, mode='w', encoding='utf-8')
        else:
            self.file = file_log
            self.filename = self.file.name()
    
    def filename_update(self):
         create_time = datetime.datetime.now()
         self.filename = f"log/{create_time:%Y-%m-%d %H-%M-%S-%f}.txt"

    def close(self):
        self.new_file = True
        self.file.close()
        #self.telebot.send_file(self.filename)

    def log(self, log, toBot = False):

        if self.new_file:
            self.filename_update()
            self.new_file = False


        if self.file.closed:
            self.file = open(self.filename, mode='w', encoding='utf-8')
    
        _timestamp = datetime.datetime.now().strftime(r'%Y.%d.%m %H:%M:%S.%f')
        print(_timestamp + "; "+str(log), file = self.file)

        #if toBot:
            #self.telebot.message(str(log))

       
   






