from azdk.azdksocket import AzdkSocket, PDSServerCommands, AzdkServerCommands, AzdkServerCmd, PDSServerCmd , call_azdk_cmd
from threading import Thread
from PyQt5.QtCore import QSettings
import os
import win32gui
import time
from azdk.azdkdb import AzdkDB
from AzdkCommands import AzdkCommands

class warden(Thread):

    connect_AZDK = [str,int]
    connect_ODS = [str,int]
    

    
     
    def __init__(self):

        current_file = os.path.abspath(__file__)
        self.directory = os.path.dirname(current_file)

        super().__init__()
        self.setName("Warden")
        self.azs = AzdkSocket()
        self.ods = AzdkSocket()
        self.settings = QSettings(self.directory+'/Ip_config.ini', QSettings.IniFormat)
        self.settings = QSettings(self.directory+'/Ip_config.ini', QSettings.IniFormat)
        self.connect_AZDK = [str(self.settings.value('Ip_azdk')),int(self.settings.value('Port_azdk'))]
        self.connect_ODS = [str(self.settings.value('Ip_ods')),int(self.settings.value('Port_ods'))]
        self.azs_answer = False
        self.ods_answer = False
        self.processes = {"azdkserver.exe" : None, "PDSServer_nogui.exe" : None}
        self.db = AzdkDB(self.directory + '/AZDKHost.xml')
        self.is_runing = True
        self.global_timeout = 5

        self.azdk_server_state_cmd = AzdkServerCmd(AzdkServerCommands(23), None, None,timeout=self.global_timeout)
        self.ods_server_state_cmd = PDSServerCmd(PDSServerCommands(3), None, None,timeout=self.global_timeout)
        self.azdk_state_cmd = self.db.createcmd(AzdkCommands(70), None, timeout=self.global_timeout)
        #self.ods_state_cmd = PDSServerCmd("GET_DISPLAY", [], None,timeout=)  нужно доделать

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

        
        self.azs = AzdkSocket(self.connect_AZDK[0], self.connect_AZDK[1], AzdkServerCommands, threadName="Warden_azdk")
        if not self.azs.waitUntilStart():
            print("Ошибка подключения AzdkServer")
        self.azs.setConnectionName("Warden",self.global_timeout)
    
        self.ods = AzdkSocket(self.connect_ODS[0], self.connect_ODS[1], PDSServerCommands, threadName="Warden_ods")
        if not self.ods.waitUntilStart():
            print("Ошибка подключения ODSServer")
        self.ods.setConnectionName("Warden",self.global_timeout)

        self.servers_state()


    def servers_state(self):
        self.azs.enqueue(self.azdk_server_state_cmd)
        azs_answer = self.azs.waitforanswer(self.azdk_server_state_cmd, self.global_timeout)
        if azs_answer:
            self.azs_answer = True
        else:
            self.azs_answer = False

        self.ods.enqueue(self.ods_server_state_cmd)
        ods_answer = self.ods.waitforanswer(self.ods_server_state_cmd, self.global_timeout)
        if ods_answer:
            self.ods_answer = True
        else:
            self.ods_answer = False

    def azdk_ods_state(self):
        if self.ods.is_alive() and self.azs.is_alive():
            call_azdk_cmd(self.azs ,self.azdk_state_cmd)
            self.db.answer(self.azdk_state_cmd.code,self.azdk_state_cmd.answer) # как сравнивать? оценивать?
            # одс код
        else:
            self.ods_answer = False
            self.azs_answer = False

    def run(self) -> None:
        while self.is_runing:
            while not self.azs_answer or not self.ods_answer:
                if not self.is_runing:
                    return
                if not self.azs.is_alive() or not self.ods.is_alive():
                    self.servers_start()
                self.activity_server()
            self.servers_state()
            self.azdk_ods_state()
