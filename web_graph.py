# Copyright (c) 2015 Tomasz Truszkowski <tomtrusz@gmail.com>
__author__ = 'Tomasz Truszkowski <tomtrusz@gmail.com>'

from page import Page
from collections import deque

import networkx as nx
import time
from networkx.readwrite import json_graph

import matplotlib.pyplot as plt
import nltk

def pages_to_graph(root_page: Page):
    graph = nx.DiGraph()

    Q = deque([root_page])
    color = { root_page.link : 1 }

    while Q:
        cur = Q.pop()
        #print("Current: {0}".format(cur.link))
        cur_link = cur.link
        for page in cur.children:
            page_link = page.link
            #print("Child: {0}".format(link))
            graph.add_edge(cur_link, page_link)
            if page_link not in color and not page.error and page.processed:
                color[page_link] = 1
                Q.appendleft(page)
        color[cur_link] = 2

    return graph

def serialize_graph(graph):
    nx.write_gexf(graph, "graph-{0}.gexf".format(int(time.time())))

def deserialize_graph(filename: str):
    return nx.read_gexf(filename)

def page_rank(graph: nx.DiGraph, root_link: str):
    num_pages = graph.number_of_nodes()
    d = 0.85

    Q = deque([root_link])
    rank = {}

    while Q:
        cur = Q.pop()
        if cur not in rank:
            indices = graph[cur]

            r = (1 - d)/num_pages
            if indices:
                r += d * (rank.get(cur, 1.0) / len(indices))
#            else:
#                print("Weird case: {0}".format(cur))
            rank[cur] = r

            for link in indices.keys():
                Q.appendleft(link)

    print(list(rank.items())[:10])
#    for key, value in rank.items():
#        print("Link: {0}\nValues: {1}".format(key, value))


def analyze(graph: nx.DiGraph, root_link: str):
    print("Graph of {0}".format(root_link))
    num_v = graph.number_of_nodes()
    num_e = graph.number_of_edges()
    #print("Shotest path:")
    #print(nx.shortest_path(graph))
    print("Number of vertices: {0}".format(num_v))
    print("Number of edges: {0}".format(num_e))
    print("Connected components:")
    #print(nx.connected_components(graph.to_undirected()))
    print("Degree:")
    print(list(nx.degree(graph))[:10])