#!/usr/bin/env python3
# Copyright (c) 2015 Tomasz Truszkowski <tomtrusz@gmail.com>
__author__ = 'Tomasz Truszkowski <tomtrusz@gmail.com>'

# Concurrency
import concurrent.futures
from queue import Queue
import time

import page
import web_graph

class LinkTraverser:
    def __init__(self, root_link):
        self.root_page = page.Page(root_link)
        self.root_page.process()
        self.work_queue = Queue()
        self.work_queue.put(self.root_page)

    def visit_one_page(self, page):
        # Check page.processed to avoid calling page.process()
        # for processed pages. The page.process() also checks
        # page.processed field, but inside the locked block.
        if not page.processed:
            return page.process()
        else:
            return False

    def traverse(self, page):
        result_children = set()
        for child in page.children:
            if self.visit_one_page(child):
                result_children.add(child)
            elif child.error:
                # False might indicate that there was an error.
                page.children.remove(child)
        return result_children

    def traverse_concurrent(self, page):
        result_children = set()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            fs = {}
            for child in page.children:
                fs[executor.submit(self.visit_one_page, child)] = child

            for future in concurrent.futures.as_completed(fs):
                child = fs[future]
                try:
                    result = future.result()
                except Exception as e:
                    print("concurrent.futures error: {0}".format(e))
                    page.children.remove(child)
                else:
                    if result:
                        result_children.add(child)
                    elif child.error:
                        page.children.remove(child)

        return result_children

    def go(self):
        count = 0
        while self.work_queue:
            cur_page = self.work_queue.get()

            # For testing purposes
            if count >= 10:
                print ("Reached the limit of processing pages. Exiting.")
                return
            count += 1

            for next_page in self.traverse(cur_page):
                self.work_queue.put(next_page)

    def go_concurrent(self):
        count = 0
        while self.work_queue:
            cur_page = self.work_queue.get()

            # For testing purposes
            if count >= 10:
                print ("Reached the limit of processing pages. Exiting.")
                return
            count += 1

            for next_page in self.traverse_concurrent(cur_page):
                self.work_queue.put(next_page)

        for next_page in self.traverse_concurrent(cur_page):
            self.work_queue.put(next_page)

if __name__ == "__main__":
    #wgraph_path = "graph-1433704861.gexf"
    wgraph_path = None
    link = "http://web.mit.edu/"

    wgraph = None
    if not wgraph_path:
        t = LinkTraverser(link)
        start = time.time()
        t.go_concurrent()
        end = time.time()
        concurrent_time = end - start

    #    print("Sequential time: {0}".format(sequential_time))
        print("Concurrent time: {0}".format(concurrent_time))

        print("Start build graph")
        start = time.time()
        wgraph = web_graph.pages_to_graph(t.root_page)
        end = time.time()
        build_graph_time = end - start
        print("Build graph time: {0}".format(build_graph_time))
        web_graph.serialize_graph(wgraph)

        t.root_page = None
        t = None
        page.Page.reset()
    else:
        wgraph = web_graph.deserialize_graph(wgraph_path)

    print(wgraph.edges())

    print("Start page rank")

    start = time.time()
    web_graph.page_rank(wgraph, link)
    end = time.time()
    page_rank_time = end - start
    print("Page rank time: {0}".format(page_rank_time))

    print("Start analyze graph")
    start = time.time()
    web_graph.analyze(wgraph, link)
    end = time.time()
    analyze_time = end - start
    print("Analyze graph time: {0}".format(analyze_time))
