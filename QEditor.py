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
from xml_creator import str_to_xml


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
        self.thread = T_hread(self.scenario, self.connect_AZDK, self.connect_ODS,self.code_editor)
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

    def __init__(self, scenario, connect_AZDK, connect_ODS,code_editor):
        
        Thread.__init__(self)
        QWidget.__init__(self)
       
        self.logger = logger()
        self.connect_AZDK = connect_AZDK
        self.connect_ODS = connect_ODS
        self.running = True
        self.presset_switcher = Presset_switcher()
        self.code_editor = code_editor
        self.scenario = scenario
        self.db = AzdkDB('AZDKHost.xml')

    def stop(self):
         self.running = False
         self.presset_switcher.stop()
         print("Script is stoped")
         self.logger.log("Script is stoped")
         self.send_text.emit(["","","","Тест был остановлен"],Color.Red)

    def true_answer(self,server,command):

        while True:
            answer = server.waitforanswer(timeout=0.1)
            
            if answer != None:
                if isinstance(command,AzdkServerCmd):
                    if answer.code == command.code :
                        print(" ANSWER "+str(answer))
                        return str(answer)
                if isinstance(command,PDSServerCmd):
                    if answer.code == command.code :
                        print(" ANSWER "+str(answer))
                        return str(answer)


    def azdk_answer(self,answer):


        if isinstance(answer,str):
            return answer
        elif isinstance(answer,bytes):
            return str(answer)
        else :
            try:
                iter(answer)
                answ = []
                for it in answer:
                    answ.append(str(it))
                return str(answ)
            except:
                return "123"

    def rus(self,answer):
        return str(answer)

    def run(self) -> None:
        
        psevdocode = self.code_editor.toPlainText()
        xml_file = "test1.xml"
        global_timeout = 999

        self.logger.log("Старт испытаний.",True)

        if psevdocode:
            self.scenario.parse(str_to_xml(psevdocode))
        elif xml_file:
            self.scenario.parse(xml_file)
        else:
            print("error")
            return

        

        for commands in self.scenario.all_commands:

            self.send_text.emit(["","","","Начало тестирования"],Color.Green)

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

            

            for command, critical in commands:

                if isinstance(command,AzdkServerCmd) and self.running:
                    azs.enqueue(command)
                    answer = azs.waitforanswer(command)
                    self.send_text.emit( [str(command.code),
                                         AzdkServerCommands.getname(command.code),
                                         "AzdkServerCmd",
                                         self.rus(answer) ],
                                         Color.Black )

                if isinstance(command,PDSServerCmd) and self.running:
                    pds.enqueue(command)
                    answer = pds.waitforanswer(command)
                    self.send_text.emit( [str(command.code),
                                         PDSServerCommands.getname(command.code),
                                         "PDSServerCmd",
                                         self.rus(answer) ],
                                         Color.Black )

                if isinstance(command,AzdkCmd) and self.running:
                
                    if critical:
                        if not call_azdk_cmd(azs, command, global_timeout):
                            self.logger.log("Критическая команда не дала ответ, тест остановлен",True)
                            self.send_text.emit(["","","","Критическая команда не дала ответ, тест остановлен"],Color.Red)
                            print("Критическая команда не дала ответ, тест остановлен")
                            pds.stop()
                            azs.stop()
                            self.scenario.all_commands.clear()
                            break
                    else:
                        call_azdk_cmd(azs, command, global_timeout)
                       

                    
                    self.send_text.emit( [str(command.code),
                                         Commands.getname(command.code),
                                         "AzdkCmd",
                                         self.azdk_answer(self.db.answer(command.code,command.answer)) ],
                                         Color.Black)

                if isinstance(command, PressetCmd):                         #Прессет код
                    self.presset_switcher.add_presset(1, Test())
                    #self.presset_switcher.exec_presset(1)

            pds.stop()
            azs.stop()
            self.logger.log("Конец испытаний.",True)
            self.send_text.emit(["","","","Конец тестирования"],Color.Green)
            self.end_test.emit()
            if self.logger:
                self.logger.close()
            self.scenario.all_commands.clear()
            self.running = True