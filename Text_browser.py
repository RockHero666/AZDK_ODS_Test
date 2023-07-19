from PyQt5 import uic
from PyQt5.QtWidgets import QWidget,QTableWidgetItem
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import os
import sys

class Color():

    White = QColor(255, 255, 255)
    Black = QColor(0, 0, 0)
    Red = QColor(255, 0, 0)
    Green = QColor(30,89,69)
    Blue = QColor(0, 0, 255)

class Text_browser(QWidget):

    def __init__(self):
        super().__init__()
        current_file = os.path.abspath(__file__)
        directory = os.path.dirname(current_file)
        uic.loadUi(directory + "/ui/Text_browser.ui", self)

        self.setWindowTitle('Log')
        titles = ['Время', 'Код', 'Команда', "Устройство", "Ответ","Результат"]
        
        self.table.setRowCount(0)
        self.table.setColumnCount(len(titles))  
        self.table.setHorizontalHeaderLabels(titles) 
        self.file = None

    def add_text(self, texts, color):
        """
        row_count = self.table.rowCount()
        for row in range(row_count):
            for col in range(6):  
                item = self.table.item(row, col)
                if item is None:
                    for i in range(6): 
                        item = QTableWidgetItem(texts[i]) 
                        if i == 0 or i == 1:  
                            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)  
                        self.table.setItem(row, i, item) 
                        self.table.item(row, i).setForeground(color)
                        self.table.resizeColumnsToContents()
                    return
        """       
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        for i in range(self.table.columnCount()): 
            txt_temp = texts[i]
            tool_tip = ''
            if i == 5:
                if txt_temp is None:
                    txt_temp = "OK"
                    color = Color.Green
                else:
                    tool_tip =  txt_temp[0]
                    txt_temp = str(txt_temp[1]) 
                    color = Color.Red 

            item = QTableWidgetItem(txt_temp) 
            item.setToolTip(tool_tip)
            if i == 0 or i == 1:  
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight) 
            item.setForeground(color) 
            self.table.setItem(row_count, i, item)  
        self.table.resizeColumnsToContents()

    def to_html(self):
        self.file = open("html.html", "w")

        html = "<html><table border=\"1\">"

        # Создание заголовка таблицы
        html += "<tr><th>Время</th><th>Код</th><th>Команда</th><th>Устройство</th><th>Ответ</th></tr>"

        for row in range(self.table.rowCount()):
            html += "<tr>"
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                if item is not None:
                    if column == 1:
                        html += "<font color=\"blue\"><td><p  align=\"right\">{}</p></td></font>".format(item.text())
                    else:
                        html += "<td>{}</td>".format(item.text())
                else:
                    html += "<td></td>"
            html += "</tr>"

        html += "</table></html>"
        self.file.write(html)
        self.file.close()

    def to_str(self):
        rows = []
        for row in range(self.table.rowCount()):
            row_items = []
            for col in range(self.table.columnCount()):
                
                item = self.table.item(row, col)
                if item is not None:
                    row_items.append(item.text())
                else:
                    row_items.append('')
            rows.append(row_items)
        return rows

    
       