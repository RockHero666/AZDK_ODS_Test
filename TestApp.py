import sys
from QEditor import Editor
from Connector import Connector
from PyQt5.QtCore import QSize, QCoreApplication
from PyQt5.QtWidgets import QMainWindow, QAction, QApplication, QMdiArea, QMdiSubWindow
from PyQt5.QtGui import QIcon, QColor
from win32api import GetSystemMetrics
from Text_browser import Text_browser
import os


class TestApp(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        
        current_file = os.path.abspath(__file__)
        directory = os.path.dirname(current_file)
    
        self.mdi = QMdiArea()
        self.setCentralWidget( self.mdi)
        self.text_browser = Text_browser()
        self.connect_widget = Connector()

        add = QAction(QIcon(directory+'/resource/add.png'), 'Добавить скрипт', self)
        add.setShortcut('Ctrl+A')
        add.setStatusTip('Добавить скрипт в центральное поле')
        add.triggered.connect(self.add_script)

        connect = QAction(QIcon(directory+'/resource/connect.png'), 'Настройки подключения', self)
        connect.setShortcut('Ctrl+Shift+C')
        connect.setStatusTip('Настройка ip адресов и портов для AZDK Server и ODS Server')
        connect.triggered.connect(self.connect_show)

        start_button = QAction(QIcon(directory+'/resource/play.png'), 'Запуск активного скрипта', self)
        start_button.setShortcut('Ctrl+P')
        start_button.setStatusTip('Запуск активного скрипта')
        start_button.triggered.connect(self.start_active_script)

        stop_button = QAction(QIcon(directory+'/resource/stop.png'), 'Остановка активного скрипта', self)
        stop_button.setShortcut('Ctrl+Shift+P')
        stop_button.setStatusTip('Остановка активного скрипта')
        stop_button.triggered.connect(self.stop_active_script)

        log_button = QAction(QIcon(directory+'/resource/log.png'), 'Показать Лог', self)
        log_button.setShortcut('Ctrl+L')
        log_button.setStatusTip('Показать Лог')
        log_button.triggered.connect(self.show_log)

        self.statusBar()

        toolbar = self.addToolBar('Tool')
        toolbar.setFixedHeight(50)
        toolbar.setIconSize(QSize(45, 45))
        toolbar.addAction(add)
        toolbar.addAction(connect)
        toolbar.addAction(start_button)
        toolbar.addAction(stop_button)
        toolbar.addAction(log_button)

        

        self.setGeometry(int(GetSystemMetrics(0)/2-650/2), int(GetSystemMetrics(1)/2-550/2), 650, 550)
        self.setWindowTitle('Исполнитель сценариев АЗДК и МЗД')
        self.show()


    def reconnect_widget(self): #привязка каждого нового сценария к логеру (из за потоков_)
        active_window = self.mdi.currentSubWindow()
        if active_window is not None:
            widget = active_window.widget()
            widget.thread.send_text[list,QColor].connect(self.text_browser.add_text)
            widget.thread.end_test.connect(self.end_test)

    def add_script(self):
        sub_window = QMdiSubWindow()
        
        editor = Editor()
        editor.start_s.connect(self.reconnect_widget)
        self.connect_widget.connect_data[str,int,str,int].connect(editor.init_ODS_AZDK)  # отправка данных каждому новому едитору
        self.connect_widget.send_data() # сигнал
        
        sub_window.setWidget(editor) 
        
        self.mdi.addSubWindow(sub_window)
        sub_window.show()

    def end_test(self):
        self.text_browser.to_html()

    def connect_show(self):
        self.connect_widget.show()

    def stop_active_script(self):
        active_window = self.mdi.currentSubWindow()
        if active_window is not None:
            widget = active_window.widget()
            if isinstance(widget, Editor):
                widget.stop()
    
    def start_active_script(self):
        active_window = self.mdi.currentSubWindow()
        if active_window is not None:
            widget = active_window.widget()
            if isinstance(widget, Editor):
                widget.start()

    def show_log(self):
        self.text_browser.show()

    def closeEvent(self, event):
        QCoreApplication.quit()


    

              


            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TestApp()
    sys.exit(app.exec_())