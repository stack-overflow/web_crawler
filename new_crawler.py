#!/usr/bin/env python3
# Copyright (c) 2015 Tomasz Truszkowski <tomtrusz@gmail.com>
__author__ = 'Tomasz Truszkowski <tomtrusz@gmail.com>'

# HTTP and HTML
import urllib.request
import urllib.robotparser

# Concurrency
import concurrent.futures
from queue import Queue

import time

import page

def get_page_text(link):
    response = urllib.request.urlopen(link)
    html = response.read()
    return html

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
                child = fs[future];
                try:
                    result = future.result()
                except Exception as e:
                    print("concurrent.futures error: {0}".format(e))
                    page.children.remove(child)
                else:
                    if result:
                        result_children.add(child)
                    else:
                        page.children.remove(child)

        return result_children

    def go(self):
        count = 0
        while self.work_queue:
            cur_page = self.work_queue.get()

            # For testing purposes
            if count >= 20:
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
            if count >= 20:
                print ("Reached the limit of processing pages. Exiting.")
                return
            count += 1

            for next_page in self.traverse_concurrent(cur_page):
                self.work_queue.put(next_page)

        for next_page in self.traverse_concurrent(cur_page):
            self.work_queue.put(next_page)

if __name__ == "__main__":
#    t = LinkTraverser("http://www.pg.gda.pl/~manus/")
#    start = time.time()
#    t.go()
#    end = time.time()
#    sequential_time = end - start
#    t.root_page = None
#    t = None
#
#    page.Page.reset()

    t = LinkTraverser("http://www.pg.gda.pl/~manus/")
    start = time.time()
    t.go_concurrent()
    end = time.time()
    concurrent_time = end - start
    t.root_page = None
    t = None

    page.Page.reset()

#    print("Sequential time: {0}".format(sequential_time))
    print("Concurrent time: {0}".format(concurrent_time))
