from azdk.azdksocket import AzdkSocket, PDSServerCommands, AzdkServerCommands, AzdkServerCmd, PDSServerCmd
from threading import Thread
from PyQt5.QtCore import QSettings
import os
import win32gui
import time

class warden(Thread):

    connect_AZDK = [str,int]
    connect_ODS = [str,int]
    azdk_state_cmd = AzdkServerCmd(AzdkServerCommands(23), [], None, 5)
    ods_state_cmd = PDSServerCmd(PDSServerCommands(3), [], None, 5)

    
     
    def __init__(self):

        current_file = os.path.abspath(__file__)
        self.directory = os.path.dirname(current_file)

        super().__init__()
        self.azs = AzdkSocket()
        self.ods = AzdkSocket()
        self.settings = QSettings(self.directory+'/Ip_config.ini', QSettings.IniFormat)
        self.settings = QSettings(self.directory+'/Ip_config.ini', QSettings.IniFormat)
        self.connect_AZDK = [str(self.settings.value('Ip_azdk')),int(self.settings.value('Port_azdk'))]
        self.connect_ODS = [str(self.settings.value('Ip_ods')),int(self.settings.value('Port_ods'))]
        self.azs_answer = False
        self.ods_answer = False
        self.processes = {"azdkserver.exe" : None, "PDSServer_nogui.exe" : None}

    def init_ODS_AZDK(self, ip_azdk, port_azdk, ip_ods, port_ods):
        self.connect_AZDK = [ip_azdk,port_azdk]
        self.connect_ODS = [ip_ods,port_ods]

    def servers_start(self): #включаем серваки
        process_names = ['azdkserver.exe', 'PDSServer_nogui.exe']
        path = self.settings.value('Path_servers')

        for process_name in process_names:
            process_path = path + process_name      
            if not win32gui.FindWindow(None, process_path) and not win32gui.IsWindow(self.processes[process_name]): # полу костыль изз за выбрать в cmd

                os.chdir(path)
                os.startfile(process_path)
                time.sleep(0.1)
                os.chdir(self.directory)
                hwnd = win32gui.FindWindow(None, process_path)
                self.processes[process_name] = hwnd


        
       

    def activity_server(self): # подключаем серваки

        if not self.azs.is_alive():
            self.azs = AzdkSocket(self.connect_AZDK[0], self.connect_AZDK[1], AzdkServerCommands, threadName="Warden_azdk")
            if not self.azs.waitUntilStart():
                print("Ошибка подключения AzdkServer")
                #return # исключение в будующем
            self.azs.setConnectionName("Warden")

        if not self.ods.is_alive():
            self.ods = AzdkSocket(self.connect_ODS[0], self.connect_ODS[1], PDSServerCommands, threadName="Warden_ods")
            if not self.ods.waitUntilStart():
                print("Ошибка подключения ODSServer")
               # return # исключение в будующем
            self.ods.setConnectionName("Warden")

        self.servers_state()


    def servers_state(self):
        self.azs.enqueue(self.azdk_state_cmd)
        azs_answer = self.azs.waitforanswer(self.azdk_state_cmd)
        if azs_answer:
            self.azs_answer = True
        else:
            self.azs_answer = False

        self.ods.enqueue(self.ods_state_cmd)
        ods_answer = self.ods.waitforanswer(self.ods_state_cmd)
        if ods_answer:
            self.ods_answer = True
        else:
            self.ods_answer = False


    def run(self) -> None:
        while True:
            while not self.azs_answer or not self.ods_answer:
                self.servers_start()
                self.activity_server()
            self.servers_state()