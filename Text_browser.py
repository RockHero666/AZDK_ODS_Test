from PyQt5 import uic
from PyQt5.QtWidgets import QWidget,QTableWidgetItem
from PyQt5.QtGui import QColor

class Color():

    White = QColor(255, 255, 255)
    Black = QColor(0, 0, 0)
    Red = QColor(255, 0, 0)
    Green = QColor(30,89,69)
    Blue = QColor(0, 0, 255)

class Text_browser(QWidget):

     def __init__(self):
        super().__init__()
        uic.loadUi('ui/Text_browser.ui', self) 

        self.setWindowTitle('Log')

        self.table.setRowCount(0)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Код', 'Команда', "Устройство", "Ответ"])
        self.file = None

     def add_text(self, texts, color):
        row_count = self.table.rowCount()
        for row in range(row_count):
            for col in range(4):
                item = self.table.item(row, col)
                if item is None:
                    for i in range(4):
                        self.table.setItem(row, i, QTableWidgetItem(texts[i]))
                        self.table.item(row, i).setForeground(color)
                        self.table.resizeColumnsToContents()
                    return

        self.table.insertRow(row_count)
        for i in range(4):
            self.table.setItem(row_count, i, QTableWidgetItem(texts[i]))
            self.table.item(row_count, i).setForeground(color)
        self.table.resizeColumnsToContents()
            
     def to_html(self):
         self.file = open("html.html", "w")

         html = "<html><table border=\"1\">"

# Создание заголовка таблицы
         html += "<tr><th></th><th>Код</th><th>Команда</th><th>Устройство</th><th>Ответ</th></tr>"

         for row in range(self.table.rowCount()):
             html += "<tr><td>{}</td>".format(row+1) # Добавление нумерации строк
             for column in range(self.table.columnCount()):
                 item = self.table.item(row, column)
                 if item is not None:
                     html += "<td>{}</td>".format(item.text())
                 else:
                     html += "<td></td>"
             html += "</tr>"
         
         html += "</table></html>"
         
         self.file.write(html)
         self.file.close()
       