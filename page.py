# Copyright (c) 2015 Tomasz Truszkowski <tomtrusz@gmail.com>
__author__ = 'Tomasz Truszkowski <tomtrusz@gmail.com>'
import urllib.request
import urllib.robotparser

import threading
import html_link_extractor

class Page:
    visited = {}
    visited_lock = threading.Lock()

    def __init__(self, link):
        self.link = link
        self.children = []
        self.processed = False
        self.page_lock = threading.RLock()
        self.error = False

    def add_child(self, link):
        with self.page_lock:
            if not Page.is_link_valid(link):
                return

            exists = [child for child in self.children if child.link == link]
            if (len(exists) == 0):
                page = Page.create(link)
                if not page.error:
                    if not link.startswith("http"):
                        print("Fixing link {0}".format(link))
                        link = Page.join_links(self.link, link)
                        print("Fixed link {0}".format(link))

                    self.children.append(page)

    def add_page_text(self, text):
        with self.page_lock:
            self.text = text

            child_links = []
            html_parser = html_link_extractor.HtmlLinkExtractor(child_links)
            html_parser.feed(self.text.decode('latin-1'))

            for link in child_links:
                self.add_child(link)

    def process(self):
        with self.page_lock:
            if not self.processed:
                try:
                    print("Trying to get: {0}".format(self.link))
                    text = Page.get_page_text(self.link)
                except Exception as e:
                    print("urllib.request error on link {0}: {1}".format(self.link, e))
                    self.error = True
                    return False
                else:
                    print("Got: {0}".format(self.link))
                    self.add_page_text(text)
                    self.set_processed(True)
                    return True
            else:
                print("Already been: {0}".format(self.link))
                return False

    def set_processed(self, value):
        with self.page_lock:
            self.processed = value

    @classmethod
    def create(cls, link):
        with cls.visited_lock:
            if link in cls.visited:
                return cls.visited[link]
            else:
                new_page = cls(link)
                cls.visited[link] = new_page
                return new_page

    @classmethod
    def is_visited(cls, link):
        with cls.visited_lock:
            return link in cls.visited

    @classmethod
    def get_page_text(cls, link):
        response = urllib.request.urlopen(link)
        html = response.read()
        return html

    @classmethod
    def join_links(cls, left, right):
        link = left
        if (left.endswith("/") and not right.startswith("/")) or\
                (not left.endswith("/") and right.startswith("/")):
            link += right
        elif right.startswith("/"):
            link += right[1:]
        else:
            link += "/" + right

        return link

    @classmethod
    def is_link_valid(cls, link):
        return link != "#"

    @classmethod
    def reset(cls):
        cls.visited = {}