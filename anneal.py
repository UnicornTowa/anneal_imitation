from copy import deepcopy
from math import exp

import networkx as nx
import anneal_common
import random

# Для начального решения будем использовать алгоритм ближайшего соседа,
# т.к. это проще и дешевле, чем искать случайный цикл
# Алгоритм ближайшего соседа
def nna(graph:nx.Graph, start_v):
    # Определяем объекты, которые будем возвращать
    out_graph = nx.DiGraph()
    path_len = 0

    # Подготовка
    vertex_count = len(graph.nodes)
    visited_count = 1
    out_graph.add_node(start_v)
    current_v = start_v

    # Помечаем вершины кроме текущей
    nx.set_node_attributes(graph, {n: {'visited': True if n == start_v else False} for n in graph.nodes()})

    # Основной цикл
    while visited_count != vertex_count:
        # Получаем все ребра, соединяющие текущую вершину с непосещенными
        edges = [edge for edge in graph.edges(current_v, data=True) if graph.nodes[edge[1]]['visited'] == False]

        # Возврат если таких вершин нет
        if len(edges) == 0:
            return out_graph, 0

        # Выбираем ребро наименьшей длины
        chosen_edge = min(edges, key=lambda x: x[2]['weight'])

        # Новая вершина цикла и длина пути до неё
        new_v = chosen_edge[1]
        weight = chosen_edge[2]['weight']

        # Добавляем элементы в выходной граф и объекты вывода, обновляем счетчик
        out_graph.add_edge(current_v, new_v, weight=weight)
        path_len += weight
        visited_count += 1

        # Помечаем вершину как посещенную, удаляем ребро из исходного графа
        graph.nodes[new_v]['visited'] = True
        current_v = new_v

    # Если вершин больше 2-х - добавляем ребро, замыкающее цикл
    if vertex_count != 1:
        if graph.has_edge(current_v, start_v) and vertex_count != 2:
            final_edge = graph.edges[current_v, start_v]
            path_len += final_edge['weight']
            out_graph.add_edge(current_v, start_v, weight=final_edge['weight'])
        else:
            return out_graph, 0
    return out_graph, path_len

# Случай когда случайные два ребра соединены
def dependent_case(graph: nx.Graph, sol: nx.DiGraph, first, a, b, last, temp):
    # Проверяем есть ли ребра
    if graph.has_edge(first, b) and graph.has_edge(a, last):
        # Вычисляем длины ребер и разницу
        partial_len = graph.edges[first, a]['weight'] + graph.edges[b, last]['weight']
        new_1_len = graph.edges[first, b]['weight']
        new_2_len = graph.edges[a, last]['weight']
        new_len = new_1_len + new_2_len
        delta = partial_len - new_len
        # Проверяем условия
        if delta > 0 or random.random() > exp(-1 * delta / temp):
            # Изменяем решение
            sol.add_edge(first, b, weight=new_1_len)
            sol.add_edge(a, last, weight=new_2_len)
            sol.add_edge(b, a, weight=graph.edges[a, b]['weight'])
            sol.remove_edge(first, a)
            sol.remove_edge(a, b)
            sol.remove_edge(b, last)
            return delta
    return 0

# Случай когда случайные два ребра не соединены
def independent_case(graph: nx.Graph, sol: nx.DiGraph, a1, a, a2, b1, b, b2, temp):
    # Проверяем есть ли ребра
    if graph.has_edge(a1, b) and graph.has_edge(b, a2) and graph.has_edge(b1, a) and graph.has_edge(a, b2):
        # Вычисляем длины путей
        partial_len = graph.edges[a1, a]['weight'] + graph.edges[a, a2]['weight'] + \
                      graph.edges[b1, b]['weight'] + graph.edges[b, b2]['weight']
        new_1_len = graph.edges[a1, b]['weight']
        new_2_len = graph.edges[b, a2]['weight']
        new_3_len = graph.edges[b1, a]['weight']
        new_4_len = graph.edges[a, b2]['weight']
        new_len = new_1_len + new_2_len + new_3_len + new_4_len
        delta = partial_len - new_len
        # Проверяем условия
        if delta > 0 or random.random() > exp(-1 * delta / temp):
            # Изменяем решение
            sol.add_edge(a1, b, weight=new_1_len)
            sol.add_edge(b, a2, weight=new_2_len)
            sol.add_edge(b1, a, weight=new_3_len)
            sol.add_edge(a, b2, weight=new_4_len)
            sol.remove_edge(a1, a)
            sol.remove_edge(a, a2)
            sol.remove_edge(b1, b)
            sol.remove_edge(b, b2)
            return delta
    return 0

# Алгоритм имитации отжига
def anneal(graph: nx.Graph, sol: nx.DiGraph, sol_len):
    if not sol:
        # Строим начальное решение
        current_solution, current_len = nna(graph, random.randint(1, len(graph.nodes)))
        # Если не нашли решение или в графе 3 вершины - ничего не изменяем
        if current_len == 0 or len(graph.nodes) == 3:
            return current_solution, current_len
    else:
        current_solution = deepcopy(sol)
        current_len = sol_len
    # Считываем параметры
    max_t, min_t, step = anneal_common.args.values()
    current_t = max_t
    # Пока температура не упала до минимальной
    while current_t > min_t:
        # Выбираем две случайных вершины
        a, b = random.sample(graph.nodes, 2)
        # Определяем инцидентные им ребра
        to_a = list(current_solution.in_edges(a, data=True))[0]
        from_a = list(current_solution.out_edges(a, data=True))[0]
        to_b= list(current_solution.in_edges(b, data=True))[0]
        from_b = list(current_solution.out_edges(b, data=True))[0]
        # Если есть совпадающие ребра, запускаем зависимый случай
        if to_b[0] == a:
            current_len -= dependent_case(graph, current_solution, to_a[0], a, b, from_b[1], current_t)
        elif to_a[0] == b:
            current_len -= dependent_case(graph, current_solution, to_b[0], b, a, from_a[1], current_t)
        # Нет совпадающих ребер - независимый случай
        else:
            current_len -= independent_case(graph, current_solution, to_a[0], a, from_a[1], to_b[0], b, from_b[1], current_t)
        # Уменьшаем температуру
        current_t -= step
    # Возвращаем решение
    return current_solution, current_len
