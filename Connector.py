from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, QSettings
from azdk.azdksocket import AzdkSocket, PDSServerCommands, AzdkServerCommands
from PyQt5.QtGui import QPixmap

class Connector(QWidget):
     connect_data = pyqtSignal(str, int,str,int)

     def __init__(self):
        super().__init__()
        uic.loadUi('ui/Connector.ui', self) 
        self.init_ui()

        self.setWindowTitle('Настройка ip')

        self.button_accept.clicked.connect(self.send_data)
        self.button_close.clicked.connect(self.close)

        self.connect_button.clicked.connect(self.connect_to_server)
        self.settings = QSettings('Ip_config.ini', QSettings.IniFormat)

        self.ip_azdk.setText(self.settings.value('Ip_azdk'))
        self.ip_ods.setText(self.settings.value('Ip_ods'))
        self.port_azdk.setValue(int(self.settings.value('Port_azdk')))
        self.port_ods.setValue(int(self.settings.value('Port_ods')))
        self.indicator.setPixmap(QPixmap("resource/indicator_def.png"))


     def connect_to_server(self):

        azs = AzdkSocket(self.ip_azdk.text(), int(self.port_azdk.text()), AzdkServerCommands)
        azs.setName("AzdkOdsTest test connect")
        azs.setConnectionName("AzdkOdsTest test connect")
        if not azs.waitUntilStart():
            print("Ошибка подключения PDSServer")
            self.indicator.setPixmap(QPixmap("resource/indicator_off.png"))
            return

        pds =AzdkSocket(self.ip_ods.text(), int(self.port_ods.text()), PDSServerCommands)
        pds.setName("AzdkOdsTest test connect")
        pds.setConnectionName("AzdkOdsTest test connect")
        if not pds.waitUntilStart():
            print("Ошибка подключения PDSServer")
            self.indicator.setPixmap(QPixmap("resource/indicator_off.png"))
            return

        if pds.is_alive() and azs.is_alive():

            self.settings.setValue('Ip_azdk', str(self.ip_azdk.text()))
            self.settings.setValue('Ip_ods', str(self.ip_ods.text()))
            self.settings.setValue('Port_azdk', str(self.port_azdk.text()))
            self.settings.setValue('Port_ods', str(self.port_ods.text()))

            self.connect_data.emit(self.ip_azdk.text(), self.port_azdk.text(),self.ip_ods.text(), self.port_ods.text())
            self.indicator.setPixmap(QPixmap("resource/indicator_on.png"))

            pds.stop()
            azs.stop()

     def init_ui(self):
         self.button_accept.clicked.connect(self.send_data)
         self.button_close.clicked.connect(self.close)

     def send_data(self):
        self.connect_data.emit(self.ip_azdk.text(), int(self.port_azdk.text()),self.ip_ods.text(), int(self.port_ods.text()))
        self.close()