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
from xml_creator import Commands


class Editor(QWidget):
     start_s = pyqtSignal()
     scenario = Scenario()
     connect_AZDK = [str,int];
     connect_ODS = [str,int];

     def __init__(self):
        super().__init__()
        uic.loadUi('ui/Editor.ui', self) 
        self.setWindowTitle('Редактор сценария')
        self.thread = None

     def update_scenario(self):
         pass # код для работы с псевдокодом в виджете и проброса в ран

     def start(self):
        self.thread = T_hread(self.scenario, self.connect_AZDK, self.connect_ODS)
        self.thread.setName("Scenario")
        self.start_s.emit()
        self.thread.start()

     def stop(self):
         if self.thread:
            self.thread.stop()

     def init_ODS_AZDK(self,ip_azdk,port_azdk,ip_ods,port_ods):

        self.connect_AZDK = [ip_azdk,port_azdk]
        self.connect_ODS = [ip_ods,port_ods]

class T_hread(Thread,QWidget):
    send_text = pyqtSignal(list,QColor)
    end_test = pyqtSignal()
    connect_AZDK = [str,int];
    connect_ODS = [str,int];

    def __init__(self, scenario, connect_AZDK, connect_ODS):
        
        Thread.__init__(self)
        QWidget.__init__(self)
       
        self.logger = logger()
        self.connect_AZDK = connect_AZDK;
        self.connect_ODS = connect_ODS;
        self.running = True
        self.presset_switcher = Presset_switcher()

        self.scenario = scenario

    def stop(self):
         self.running = False
         self.presset_switcher.stop()
         print("Script is stoped")
         self.logger.log("Script is stoped")

    def true_answer(self,server,command):

        while True:
            answer = server.waitforanswer(timeout=0.1)
            
            if answer != None:
                if isinstance(command,AzdkServerCmd):
                    if answer.code == command.code :
                        return str(answer)
                if isinstance(command,PDSServerCmd):
                    return str(answer)


    def run(self) -> None:
        
        self.logger.log("Старт испытаний.",True)

        self.scenario.parse("test1.xml")

        db = AzdkDB('AZDKHost.xml')

        azs = AzdkSocket(self.connect_AZDK[0], self.connect_AZDK[1], AzdkServerCommands,
                                                True, "AzdkServerCommands", self.logger)
        if not azs.waitUntilStart():
            self.send_text.emit(["","","","Ошибка подключения AzdkServer"],Color.Red)
            self.logger.log("Ошибка подключения AzdkServer",True)
            print("Ошибка подключения AzdkServer")
            return
        azs.setConnectionName("AzdkOdsTestApp")

        pds = AzdkSocket(self.connect_ODS[0], self.connect_ODS[1], PDSServerCommands,
                                              True, "PDSServerCommands", self.logger)
        if not pds.waitUntilStart():
            self.send_text.emit(["","","","Ошибка подключения AzdkServer"],Color.Red)
            self.logger.log("Ошибка подключения AzdkServer",True)
            print("Ошибка подключения AzdkServer")
            return
        pds.setConnectionName("AzdkOdsTestApp")

        global_timeout = 0.5

        for command in self.scenario.commands:

            if isinstance(command[0],AzdkServerCmd) and self.running:
                azs.enqueue(command[0])
                self.send_text.emit( [str(command[0].code),
                                     AzdkServerCommands.getname(command[0].code),
                                     "AzdkServerCmd",
                                     self.true_answer(azs,command[0]) ],
                                     Color.Black )

            if isinstance(command[0],PDSServerCmd) and self.running:
                pds.enqueue(command[0])
                self.send_text.emit( [str(command[0].code),
                                     PDSServerCommands.getname(command[0].code),
                                     "PDSServerCmd",
                                     self.true_answer(pds,command[0]) ],
                                     Color.Black )

            if isinstance(command[0],AzdkCmd) and self.running:
            
                if command[1]:
                    if not call_azdk_cmd(azs, command[0], global_timeout):
                        self.logger.log("Критическая команда не дала ответ, тест остановлен",True)
                        self.send_text.emit(["","","","Критическая команда не дала ответ, тест остановлен"],Color.Red)
                        print("Критическая команда не дала ответ, тест остановлен")
                        pds.stop()
                        azs.stop()
                        self.scenario.commands.clear()
                        break
                else:
                    call_azdk_cmd(azs, command[0], global_timeout)

                self.send_text.emit( [str(command[0].code),Commands.findname(command[0].code),"AzdkCmd",str(command[0].answer) ],Color.Black)

            if isinstance(command[0], PressetCmd):                         #Прессет код
                self.presset_switcher.add_presset(1, Test())
                #self.presset_switcher.exec_presset(1)

        pds.stop()
        azs.stop()
        self.logger.log("Конец испытаний.",True)
        self.end_test.emit()
        if self.logger:
            self.logger.close()
        self.scenario.commands.clear()
        self.running = True