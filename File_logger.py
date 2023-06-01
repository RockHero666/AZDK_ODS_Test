import datetime
from threading import Lock
from telebot import TeleBot

class logger:

    def __init__(self, filename = None,file_log = None):

        self.telebot = TeleBot("5811298447:AAF0--61uBVvKgFvMeYs76fB1QjmhaihU-Y", -822387173)

        if not filename:
            create_time = datetime.datetime.now()
            self.filename = f"log/{create_time:%Y-%m-%d %H-%M-%S-%f}.txt"

        if not file_log:
            self.file = open(self.filename, mode='a', encoding='utf-8')
        else:
            self.file = file_log
            self.filename = self.file.name()

        self.mutex = Lock()
       
    def close(self):
        self.file.close()
        #self.telebot.send_file(self.filename)

    def log(self, log, toBot = False):

        if self.file.closed:
            self.file = open(self.filename, mode='a', encoding='utf-8')
    
        _timestamp = datetime.datetime.now().strftime(r'%Y.%d.%m %H:%M:%S.%f')
        print(_timestamp + "; "+str(log), file = self.file)

        #if toBot:
            #self.telebot.message(str(log))

       
   






