# Основное окно
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPainter, QColor, QCloseEvent
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView, \
    QTextEdit

import anneal
import anneal_common
import anneal_viz


# Основной класс
class MainWindow(QMainWindow):
    # Конструктор класса
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('nodes.png'))  # Иконка

        # Текстовые поля
        self.input_title = QLabel('Input Graph', self)
        self.input_title.setFont(anneal_common.title_f)
        self.input_title.move(10, 10)
        self.input_title.setFixedWidth(300)

        self.input_title = QLabel('Control', self)
        self.input_title.setFont(anneal_common.title_f)
        self.input_title.move(10, 560)
        self.input_title.setFixedWidth(300)

        self.output_title = QLabel('Output Graph', self)
        self.output_title.setFont(anneal_common.title_f)
        self.output_title.move(10, 640)
        self.output_title.setFixedWidth(300)

        self.results_title = QLabel('Edge Table', self)
        self.results_title.setFont(anneal_common.title_f)
        self.results_title.move(980, 10)
        self.results_title.setFixedWidth(300)

        self.results_title = QLabel('Instructions & Results', self)
        self.results_title.setFont(anneal_common.title_f)
        self.results_title.move(980, 760)
        self.results_title.setFixedWidth(300)

        # Кнопки
        self.start_button = QPushButton('Start', self)
        self.start_button.setFont(anneal_common.f)
        self.start_button.move(20, 600)
        self.start_button.setFixedWidth(200)
        self.start_button.clicked.connect(self.start)

        self.reset_button = QPushButton('Reset Graph', self)
        self.reset_button.setFont(anneal_common.f)
        self.reset_button.move(220, 600)
        self.reset_button.setFixedWidth(200)
        self.reset_button.clicked.connect(self.reset)

        self.complete_button = QPushButton('Complete', self)
        self.complete_button.setFont(anneal_common.f)
        self.complete_button.move(420, 600)
        self.complete_button.setFixedWidth(200)
        self.complete_button.clicked.connect(self.complete_graph)

        self.params_button = QPushButton('Options', self)
        self.params_button.setFont(anneal_common.f)
        self.params_button.move(620, 600)
        self.params_button.setFixedWidth(200)
        self.params_button.clicked.connect(self.open_options)


        # Установка размеров окна и заголовка
        scaler = 400
        self.setFixedSize(4*scaler, 3*scaler)
        self.setWindowTitle('Anneal Imitation Algorithm')

        # Привязываем редактируемый входной граф
        self.g_input = anneal_viz.GraphWidgetEditable(self)
        self.g_input.move(10, 50)
        self.g_input.setFixedSize(950, 500)
        self.layout().addWidget(self.g_input)

        self.g_input.installEventFilter(self)

        # Привязываем нередактируемый выходной граф
        self.g_output = anneal_viz.GraphWidget(self)
        self.g_output.move(10, 680)
        self.g_output.setFixedSize(950, 500)
        self.layout().addWidget(self.g_output)
        self.path_len = 0

        # Таблица вывода
        self.table = QTableWidget(self)
        self.table_size = 0
        self.table.setColumnCount(3)
        self.table.setFixedSize(600, 700)
        self.table.move(980, 50)
        self.table.setHorizontalHeaderItem(0, QTableWidgetItem('Vertex 1'))
        self.table.setHorizontalHeaderItem(1, QTableWidgetItem('Vertex 2'))
        self.table.setHorizontalHeaderItem(2, QTableWidgetItem('Path length'))
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 200)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.setRowCount(0)
        self.table.itemChanged.connect(self.table_edited)

        # Текстовое поле для вывода инструкций и результата
        self.results_field = QTextEdit(self)
        self.results_field.move(980, 800)
        self.results_field.setFixedSize(600, 380)
        self.results_field.setFont(anneal_common.f)
        self.results_field.setText(anneal_common.default_text)
        self.results_field.setReadOnly(True)

        self.options_window = None

    def open_options(self):
        self.options_window = anneal_viz.OptionsWindow()
        self.options_window.show()
        self.options_window.installEventFilter(self)

    # Достройка графа до полного
    def complete_graph(self):
        self.g_input.complete()

    # Демонстрация выходного графа
    def update_res(self):
        self.g_output.pos = {n: self.g_input.pos[n] for n in self.g_output.G.nodes}
        self.g_output.vertex_count = len(self.g_output.G.nodes)
        self.g_output.update_graph()
        self.results_field.setText(
            f'Solution: {anneal_common.get_path(self.g_output.G)}\n'
            f'Path length: {round(self.path_len, 2)}')

    # Изменение веса ребра при редактировании таблицы
    def table_edited(self, item):
        self.path_len = 0
        if item is not None:
            row = item.row()
            start_v = int(self.table.item(row, 0).text())
            end_v = int(self.table.item(row, 1).text())
            # Отлов исключений
            try:
                new_weight = float(item.text())
                if new_weight <= 0:
                    raise ValueError('Вес <= 0')
            except:
                anneal_common.input_error('Некорректный вес ребра')
                self.table.blockSignals(True)
                self.table.setItem(row, 2, QTableWidgetItem(str(round(self.g_input.G[start_v][end_v]['weight'], 2))))
                self.table.item(row, 2).setTextAlignment(Qt.AlignCenter)
                self.table.blockSignals(False)
                return
            self.g_input.G.edges[start_v, end_v]['weight'] = new_weight

    # Функция делает редактируемой только последний элемент ряда таблицы
    def set_table_row_edit_flags(self, row):
        self.table.item(row, 0).setFlags(self.table.item(row, 0).flags() & ~Qt.ItemIsEditable)
        self.table.item(row, 1).setFlags(self.table.item(row, 1).flags() & ~Qt.ItemIsEditable)
        self.table.item(row, 2).setFlags(self.table.item(row, 2).flags() | Qt.ItemIsEditable)

    # Сброс графа и результатов
    def reset(self):
        self.g_input.clear_graph()
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table_size = 0
        self.g_output.clear_graph()
        self.results_field.setText(anneal_common.default_text)
    # Отлов событий
    def eventFilter(self, obj, event):
        # Добавление ряда таблицы при построении нового ребра
        if obj == self.g_input and event.type() == anneal_common.NewEdge.Type:
            self.table.blockSignals(True)
            self.table.insertRow(self.table_size)
            self.table.setItem(self.table_size, 0, QTableWidgetItem(str(event.start)))
            self.table.setItem(self.table_size, 1, QTableWidgetItem(str(event.end)))
            self.table.setItem(self.table_size, 2, QTableWidgetItem(str(round(event.weight, 2))))
            self.set_table_row_edit_flags(self.table_size)
            for i in range(3):
                self.table.item(self.table_size, i).setTextAlignment(Qt.AlignCenter)
            self.table_size += 1
            self.table.blockSignals(False)
            return True
        return super().eventFilter(obj, event)
    # Деструктор, закрывающий все окна
    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.options_window and self.options_window.isVisible():
            self.options_window.close()
        a0.accept()



    # Запуск алгоритма
    def start(self):
        # Проверка на наличие графа
        if len(self.g_input.G.nodes) == 0:
            anneal_common.input_error('Граф пуст')
            return
        sol = None
        if self.path_len != 0 and self.g_input.G.number_of_nodes() == self.g_output.G.number_of_nodes():
            sol = self.g_output.G
        graph, self.path_len = anneal.anneal(self.g_input.G, sol, self.path_len)
        # Очистка выходного графа
        self.g_output.clear_graph()
        # Запуск и установка результатов
        self.g_output.G = graph
        self.update_res()

    # Разметка окна
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor(0, 0, 0))
        painter.drawRect(10, 560, 950, 110)
        painter.drawRect(10, 50, 950, 500)
        painter.drawRect(10, 680, 950, 500)
        painter.drawRect(980, 50, 600, 700)
        painter.drawRect(980, 800, 600, 380)



# Запуск приложения
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
