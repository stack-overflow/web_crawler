# Copyright (c) 2015 Tomasz Truszkowski <tomtrusz@gmail.com>
import os

__author__ = 'Tomasz Truszkowski <tomtrusz@gmail.com>'
import urllib.request
import urllib.robotparser
from urllib.parse import urljoin

import threading

import html_link_extractor
import html_text_extractor
import robots_info

class Page:
    visited = {}
    visited_lock = threading.Lock()
    root_url = None

    def __init__(self, link, robots=None):
        self.link = link
        self.children = []
        self.processed = False
        self.page_lock = threading.RLock()
        self.error = False
        self.robots = robots

    def save(self):
        path = "/".join(self.link.split("/")[3:])
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "wb") as f:
            f.write(self.text)
        with open(path+".txt", "w") as f:
            f.write(self.normalized_text)

    def add_child(self, link):
        with self.page_lock:
            if not Page.is_link_valid(link):
                return

            exists = [child for child in self.children if child.link == link]
            if (len(exists) == 0):
                if not link.startswith("http"):
                    # print("Fixing link {0}".format(link))
                    link = Page.join_links(self.link, link)
                    # print("Fixed link {0}".format(link))

                if self.can_fetch(link):
                    page = Page.create(link, self.robots)
                    if not page.error:
                        self.children.append(page)

    def parse_page_text(self, text):
        with self.page_lock:
            self.text = text

            child_links = []
            html_parser = html_link_extractor.HtmlLinkExtractor(child_links)
            html_parser.feed(self.text.decode('ascii', 'ignore'))

            html_parser = html_text_extractor.HtmlTextExtractor()
            html_parser.feed(self.text.decode('ascii', 'ignore'))
            self.normalized_text = html_parser.text

            for link in child_links:
                self.add_child(link)

    def fetch_robots(self):
        try:
            robots_link = Page.join_links(self.link, "/robots.txt")
            req = urllib.request.Request(robots_link, method='HEAD')
            f = urllib.request.urlopen(req, timeout=8)
        except:
            self.robots = None
            pass
        else:
            robots_text = Page.get_page_text(robots_link)
            if robots_info.RobotsInfo.is_robots_content(robots_text.decode('ascii', 'ignore')):
                print("Got robots.txt: {0}".format(robots_link))
                self.robots = robots_info.RobotsInfo(self.link, robots_link)

    def can_fetch(self, link):
        if self.robots:
            return self.robots.can_fetch(link) and Page.is_link_valid(link) and Page.is_link_from_domain(link)
        else:
            return Page.is_link_valid(link) and Page.is_link_from_domain(link)

    def process(self):
        with self.page_lock:
            if not self.processed:
                try:
                    text = Page.get_page_text(self.link)
                except Exception as e:
                    print("urllib.request error on link {0}: {1}".format(self.link, e))
                    self.error = True
                    return False
                else:
                    print("Got: {0}".format(self.link))
                    self.fetch_robots()
                    self.parse_page_text(text)
                    self.set_processed(True)
                    return True
            else:
                print("Already been: {0}".format(self.link))
                return False

    def set_processed(self, value):
        with self.page_lock:
            self.processed = value

    @classmethod
    def create(cls, link, robots):
        with cls.visited_lock:
            if link in cls.visited:
                return cls.visited[link]
            else:
                # Pass robots only when base_url of the robots.txt
                # is the prefix of the link.
                if not robots or not link.startswith(robots.base_url):
                    robots = None
                new_page = cls(link, robots)
                cls.visited[link] = new_page
                return new_page

    @classmethod
    def is_visited(cls, link):
        with cls.visited_lock:
            return link in cls.visited

    @classmethod
    def get_page_text(cls, link):
        response = urllib.request.urlopen(link, timeout=8)
        html = response.read()
        return html

    @classmethod
    def join_links(cls, left, right):
        return urljoin(left, right)

    @classmethod
    def skip_http_prefix(cls, link: str):
        if link.startswith("http://"):
            return link[7:]
        elif link.startswith("https://"):
            return link[8:]
        else:
            return link

    @classmethod
    def is_link_valid(cls, link: str):
        return link != "#"

    @classmethod
    def is_link_from_domain(cls, link: str):
        if not link:
            return False
        is_from_domain = link.startswith(cls.root_url)
        if not is_from_domain:
            normalized_link = Page.skip_http_prefix(link)
            is_from_domain = normalized_link.startswith(cls.normalized_root_url)
        return link != "#" and is_from_domain

    @classmethod
    def reset(cls):
        cls.visited = {}

    @classmethod
    def set_root_url(cls, root_url):
        with cls.visited_lock:
            cls.root_url = root_url
            print (cls.root_url)
            cls.normalized_root_url = Page.skip_http_prefix(root_url)