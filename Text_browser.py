from PyQt5 import uic
from PyQt5.QtWidgets import QWidget,QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QColor


class Color():

    White = QColor(255, 255, 255)
    Black = QColor(0, 0, 0)
    Red = QColor(255, 0, 0)
    Green = QColor(0, 255, 0)
    Blue = QColor(0, 0, 255)


class Text_browser(QWidget):

     def __init__(self):
        super().__init__()
        uic.loadUi('ui/Text_browser.ui', self) 

        
        self.table.setRowCount(4)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Код', 'Команда', "Устройство", "Ответ"])


        self.table.setItem(0, 0, QTableWidgetItem('Text 1'))
        self.table.item(0, 0).setForeground(Color.Green)
        
     def add_text(self, texts, color):
        # определяем количество строк таблицы
        row_count = self.table.rowCount()

        # проходим по строкам таблицы
        for row in range(row_count):
            # проходим по столбцам таблицы
            for col in range(4):
                # получаем ячейку по индексам строки и столбца
                item = self.table.item(row, col)
                # если ячейка пустая, то записываем в нее текст из списка и выходим из цикла
                if item is None:
                    for i in range(4):
                        self.table.setItem(row, i, QTableWidgetItem(texts[i]))
                        self.table.item(row, i).setForeground(color)
                    return

        # если все ячейки заполнены текстом, то добавляем новую строку и вставляем текст в ячейки этой строки
        self.table.insertRow(row_count)
        for i in range(4):
            self.table.setItem(row_count, i, QTableWidgetItem(texts[i]))
            self.table.item(row_count, i).setForeground(color)  
       
'''
     def add_text(self,text):
         self.textBrowser.append(text) 


     def add_text(self, text, color):
        self.table.setItem(0, 0, QTableWidgetItem(text))
        self.table.item(0, 0).setForeground(color)
'''
'''
     def add_text(self, text, color):
         # определяем количество строк таблицы
         row_count = self.table.rowCount()

         # проходим по строкам таблицы
         for row in range(row_count):
             # проходим по столбцам таблицы
             for col in range(4):
                 # получаем ячейку по индексам строки и столбца
                 item = self.table.item(row, col)
                 # если ячейка пустая, то записываем в нее текст и выходим из цикла
                 if item is None:
                     self.table.setItem(row, col, QTableWidgetItem(text))
                     self.table.item(row, col).setForeground(color)
                     return

         # если все ячейки заполнены текстом, то добавляем новую строку и вставляем текст в первую не заполненную ячейку этой строки
         self.table.insertRow(row_count)
         self.table.setItem(row_count, 0, QTableWidgetItem(text))
         self.table.item(row_count, 0).setForeground(color)
'''
     