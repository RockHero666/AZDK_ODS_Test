from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from threading import Thread
from PyQt5.QtCore import pyqtSignal
from azdk.azdksocket import AzdkSocket, PDSServerCmd, AzdkServerCmd, call_azdk_cmd , PDSServerCommands, AzdkServerCommands
from azdk.azdkdb import AzdkDB, AzdkCmd
from Scenario import Scenario, PressetCmd
from Presset_tests import Presset_switcher
from PyQt5.QtGui import  QColor
from File_logger import logger
from azdk.pds_utils import Test
from Text_browser import  Color
from AzdkCommands import AzdkCommands
from xml_creator import str_to_xml
import datetime
import time
import os

class Editor(QWidget):
     start_s = pyqtSignal()
     scenario = Scenario()
     connect_AZDK = [str,int]
     connect_ODS = [str,int]

     def __init__(self):
        super().__init__()
        current_file = os.path.abspath(__file__)
        directory = os.path.dirname(current_file)
        uic.loadUi(directory + "/ui/Editor.ui", self) 
        self.setWindowTitle('Редактор сценария')
        self.thread = None

     def update_scenario(self):
         pass # код для работы с псевдокодом в виджете и проброса в ран

     def start(self):
        self.thread = T_hread(self.scenario, self.connect_AZDK, self.connect_ODS,self.code_editor)
        self.thread.setName("Scenario")
        self.start_s.emit()
        self.thread.start()

     def stop(self):
         if self.thread:
            self.thread.stop()

     def init_ODS_AZDK(self, ip_azdk, port_azdk, ip_ods, port_ods):
        self.connect_AZDK = [ip_azdk,port_azdk]
        self.connect_ODS = [ip_ods,port_ods]

class T_hread(Thread,QWidget):
    send_text = pyqtSignal(list,QColor)
    end_test = pyqtSignal()
    connect_AZDK = [str,int]
    connect_ODS = [str,int]

    def __init__(self, scenario, connect_AZDK, connect_ODS, code_editor):
        
        Thread.__init__(self)
        QWidget.__init__(self)
       
        current_file = os.path.abspath(__file__)
        self.directory = os.path.dirname(current_file)
        self.logger = logger()
        self.connect_AZDK = connect_AZDK
        self.connect_ODS = connect_ODS
        self.running = True
        self.presset_switcher = Presset_switcher()
        self.code_editor = code_editor
        self.scenario = scenario
        self.db = AzdkDB(self.directory + '/AZDKHost.xml')

    def stop(self):
         self.running = False
         self.presset_switcher.stop()
         print("Script is stoped")
         self.logger.log("Script is stoped")
         self.send_text.emit(["","","","Тест был остановлен"],Color.Red)


    def rus(self,answer):
        return str(answer)

    def run(self) -> None:
        
        psevdocode = self.code_editor.toPlainText()
        xml_file = self.directory +"/test1.xml"
        global_timeout = 5

        self.logger.log("Старт испытаний.",True)

        if psevdocode:
            self.scenario.parse(str_to_xml(psevdocode))
        elif xml_file:
            self.scenario.parse(xml_file)
        else:
            print("error")
            return

        

        for commands in self.scenario.all_commands:

            current_time = datetime.datetime.now()   
            mic_s =current_time.microsecond
            current_time = current_time.strftime("%H:%M:%S")
            mil_s = mic_s // 1000
            current_time += f".{mil_s:03}"

            self.send_text.emit([current_time,"","","","Начало тестирования"],Color.Green)

            azs = AzdkSocket(self.connect_AZDK[0], self.connect_AZDK[1], AzdkServerCommands,
                                                    True, "AzdkServerCommands", self.logger)
            if not azs.waitUntilStart():
                self.send_text.emit([current_time,"","","","Ошибка подключения AzdkServer"],Color.Red)
                self.logger.log("Ошибка подключения AzdkServer",True)
                print("Ошибка подключения AzdkServer")
                return
            azs.setConnectionName("AzdkOdsTestApp")

            pds = AzdkSocket(self.connect_ODS[0], self.connect_ODS[1], PDSServerCommands,
                                                  True, "PDSServerCommands", self.logger)
            if not pds.waitUntilStart():
                self.send_text.emit([current_time,"","","","Ошибка подключения PDSServer"],Color.Red)
                self.logger.log("Ошибка подключения PDSServer",True)
                print("Ошибка подключения PDSServer")
                return
            pds.setConnectionName("AzdkOdsTestApp")

            

            for command, critical in commands:

                current_time = datetime.datetime.now()   
                mic_s =current_time.microsecond
                current_time = current_time.strftime("%H:%M:%S")
                mil_s = mic_s // 1000
                current_time += f".{mil_s:03}"

                if isinstance(command,AzdkServerCmd) and self.running:
                    azs.enqueue(command)
                    time.sleep(0.1)
                    answer = azs.waitforanswer(command)
                    self.send_text.emit( [current_time,
                                          str(command.code),
                                         AzdkServerCommands.getdescr(command.code),
                                         "ASC",
                                         self.rus(answer) ],
                                         Color.Black )

                if isinstance(command,PDSServerCmd) and self.running:
                    pds.enqueue(command)
                    time.sleep(0.1)
                    answer = pds.waitforanswer(command)
                    self.send_text.emit( [current_time,
                                          str(command.code),
                                         PDSServerCommands.getdescr(command.code),
                                         "PSC",
                                         self.rus(answer) ],
                                         Color.Black )

                if isinstance(command,AzdkCmd) and self.running:
                
                    if critical:
                        if not call_azdk_cmd(azs, command,timeout=global_timeout):
                            self.logger.log("Критическая команда не дала ответ, тест остановлен",True)
                            self.send_text.emit([current_time,"","","","Критическая команда не дала ответ, тест остановлен"],Color.Red)
                            print("Критическая команда не дала ответ, тест остановлен")
                            pds.stop()
                            azs.stop()
                            self.scenario.all_commands.clear()
                            break
                        else:
                            if command.answer == b"":
                                command.answer = "Ответ от устройства получен"
                    else:
                        if not call_azdk_cmd(azs, command,timeout=global_timeout):
                            command.answer = "Критическая команда не дала ответ, тест продолжается"
                            print("Критическая команда не дала ответ, тест продолжается")
                        else:
                            if command.answer == b"":
                                command.answer = "Ответ от устройства получен"

                    if command.code == 1 or command.code == 23 or command.code == 24 or command.code == 25:
                        time.sleep(1)

                    

                    self.send_text.emit( [current_time,
                                          str(command.code),
                                         self.db.cmd(command.code)['name'],
                                         "AC",
                                         self.db.answer_str(command) ],
                                         Color.Black)
                    

                if isinstance(command, PressetCmd):                         #Прессет код
                    self.presset_switcher.add_presset(1, Test())
                    #self.presset_switcher.exec_presset(1)

            pds.stop()
            azs.stop()
            self.logger.log("Конец испытаний.",True)
            self.send_text.emit([current_time,"","","","Конец тестирования"],Color.Green)
            self.end_test.emit()
            if self.logger:
                self.logger.close()
            self.scenario.all_commands.clear()
            self.running = True