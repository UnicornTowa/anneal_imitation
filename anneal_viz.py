# Прочие отображаемые объекты
from itertools import combinations

import matplotlib
import networkx as nx
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication, QLabel, QLineEdit, QPushButton
from matplotlib import pyplot as plt

import anneal_common

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Вычисление квадратов расстояний между точкой и массивом точек
def dist_multi(point, points):
    return np.sum((points - point)**2, axis=1)

# Вычисление расстояния между двумя точками
def dist(point_a, point_b):
    return ((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2) ** (1 / 2)

# Класс отображаемого графа
class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        # Создание графа и его параметров
        self.G = nx.Graph()

        self.pos = {}
        self.vertex_count = 0
        self.selected_vertex = None

        # отображение графа с помощью Matplotlib
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.axis('off')
        self.fig.tight_layout()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(parent)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    # Отрисовка графа
    def update_graph(self):
        nx.draw_networkx_edges(self.G, self.pos, width=2.5, edge_color='k', ax=self.ax)
        nx.draw_networkx_nodes(self.G, self.pos,
                               node_size=550,
                               node_color=['g' if n + 1 == self.selected_vertex else 'b' for n in range(self.vertex_count)],
                               edgecolors='k', ax=self.ax)
        nx.draw_networkx_labels(self.G, self.pos, font_size=15, font_color='w', font_family='Arial', ax=self.ax)
        self.canvas.draw_idle()
        self.fig.tight_layout()
    def clear_fig(self):
        self.ax.clear()
        self.ax.axis('off')
        self.fig.tight_layout()
    # Очистка графа
    def clear_graph(self):
        self.G.clear()
        self.pos.clear()
        self.vertex_count = 0
        self.selected_vertex = None
        self.clear_fig()
        self.update_graph()

# Класс редактируемого отображаемого графа
class GraphWidgetEditable(GraphWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # Настройка осей изображения
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.fig.tight_layout()

        self.vertex_count = 0
        self.selected_vertex = None

        # Привязка функций, вызываемых по клику мыши
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)

    # Достройка графа до полного
    def complete(self):
        for a, b in combinations(self.G.nodes, 2):
            if not self.G.has_edge(a, b):
                self.add_edge(a, b, weight=dist(self.pos[a], self.pos[b]))
        self.update_graph()

    # Очистка графа с настройкой осей
    def clear_fig(self):
        super().clear_fig()
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.fig.tight_layout()

    # Отправка события в основной класс при добавлении ребра
    def send_edge(self, start, end, weight=None):
        event = anneal_common.NewEdge(start, end, weight)
        QApplication.postEvent(self, event)

    # Добавление вершины
    def add_vertex(self, pos:np.ndarray((1, 2), dtype=int)):
        self.vertex_count += 1
        self.G.add_node(self.vertex_count)
        self.pos[self.vertex_count] = pos

    # Добавление ребра
    def add_edge(self, u:int, v:int, weight=None):
        if (u, v) not in self.G.edges:
            self.G.add_edge(u, v, weight=weight)
            self.send_edge(u, v, weight)

    # Перевод внутренних координат графика во внешние
    def in2out(self, p):
        return self.ax.transData.transform((p[0], p[1]))

    # -//- внешних во внутренние
    def out2in(self, p):
        return self.ax.transData.inverted().transform((p[0], p[1]))

    # Событие по отпускании кнопки мыши
    def on_release(self, event):
        if event.button == Qt.LeftButton:
            point = (event.x, event.y)
            # Если нет выбранной вершины - строим новую
            if not self.selected_vertex:
                self.add_vertex(self.out2in(point))
                self.update_graph()
            else:
                # Если есть выбранная вершина ищем ближайшую
                closest = self.get_closest(point)
                # Если ближайшая вершина на небольшом расстоянии, строим ребро между выбранной и ближайшей
                if closest and closest != self.selected_vertex:
                    self.add_edge(self.selected_vertex, closest, weight=dist(self.pos[self.selected_vertex], self.pos[closest]))
                    self.selected_vertex = None
                    self.update_graph()

    # Получение ближайшей вершины
    def get_closest(self, click_coords):
        # Считаем расстояния во внешних координатах до всех вершин
        distances = dist_multi(click_coords, np.apply_along_axis(self.in2out, 1, np.array(list(self.pos.values()))))
        closest_vertex = np.argmin(distances) + 1
        # Если расстояние до ближайшей достаточно мало, возвращаем ее
        if distances[closest_vertex - 1] > 600:
            return
        else:
            return closest_vertex

    # По клику выбираем ближайшую вершину (если она есть)
    def on_click(self, event):
        if event.button == Qt.LeftButton and self.vertex_count != 0:
            point = (event.x, event.y)
            closest = self.get_closest(point)
            self.selected_vertex = closest
            self.update_graph()

class OptionsWindow(QWidget):
    def __init__(self, parent=None):
        super(OptionsWindow, self).__init__(parent)
        self.setWindowTitle("Options")
        self.resize(350, 275)
        self.setWindowIcon(QIcon('settings.png'))

        self.output_title = QLabel('Parameters', self)
        self.output_title.setFont(anneal_common.title_f)
        self.output_title.move(10, 10)
        self.output_title.setFixedWidth(160)

        self.max_t_label = QLabel('Max temperature:', self)
        self.max_t_label.setFont(anneal_common.f)
        self.max_t_label.move(10, 40)
        self.max_t_label.setFixedWidth(160)
        self.max_t_input = QLineEdit(self)
        self.max_t_input.setFont(anneal_common.f)
        self.max_t_input.move(170, 40)
        self.max_t_input.setFixedWidth(100)
        self.max_t_input.setValidator(anneal_common.only_int)
        self.max_t_input.setText(str(anneal_common.args['max_t']))
        self.max_t_input.setPlaceholderText('int, >=0')

        self.min_t_label = QLabel('Min temperature:', self)
        self.min_t_label.setFont(anneal_common.f)
        self.min_t_label.move(10, 70)
        self.min_t_label.setFixedWidth(160)
        self.min_t_input = QLineEdit(self)
        self.min_t_input.setFont(anneal_common.f)
        self.min_t_input.move(170, 70)
        self.min_t_input.setFixedWidth(100)
        self.min_t_input.setValidator(anneal_common.only_int)
        self.min_t_input.setText(str(anneal_common.args['min_t']))
        self.min_t_input.setPlaceholderText('int, >=0')

        self.steps_label = QLabel('Step:', self)
        self.steps_label.setFont(anneal_common.f)
        self.steps_label.move(10, 100)
        self.steps_label.setFixedWidth(160)
        self.steps_input = QLineEdit(self)
        self.steps_input.setFont(anneal_common.f)
        self.steps_input.move(170, 100)
        self.steps_input.setFixedWidth(100)
        self.steps_input.setValidator(anneal_common.only_int)
        self.steps_input.setText(str(anneal_common.args['step']))
        self.steps_input.setPlaceholderText('int, >1')

        self.set_button = QPushButton('Set', self)
        self.set_button.setFont(anneal_common.f)
        self.set_button.move(10, 150)
        self.set_button.setFixedWidth(100)
        self.set_button.clicked.connect(self.set_params)

        self.reset_button = QPushButton('Reset', self)
        self.reset_button.setFont(anneal_common.f)
        self.reset_button.move(120, 150)
        self.reset_button.setFixedWidth(100)
        self.reset_button.clicked.connect(self.reset_params)
    def set_params(self):
        max_t = int(self.max_t_input.text())
        min_t = int(self.min_t_input.text())
        cool_rate = float(self.steps_input.text())
        if max_t < 0 or min_t < 0:
            anneal_common.input_error('Отрицательная температура')
            return
        if cool_rate <= 0:
            anneal_common.input_error('Некорректный шаг охлаждения')
            return
        anneal_common.args['max_t'] = max_t
        anneal_common.args['min_t'] = min_t
        anneal_common.args['step'] = cool_rate
        self.close()
    def reset_params(self):
        anneal_common.reset_args()
        self.min_t_input.setText(str(anneal_common.args['min_t']))
        self.min_t_input.setText(str(anneal_common.args['min_t']))
        self.steps_input.setText(str(anneal_common.args['step']))
        self.close()