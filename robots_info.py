# Copyright (c) 2015 Tomasz Truszkowski <tomtrusz@gmail.com>
__author__ = 'Tomasz Truszkowski <tomtrusz@gmail.com>'
import urllib.robotparser

class RobotsInfo:
    def __init__(self, base_url, link):
        self.base_url = base_url
        self.link = link
        self.parser = urllib.robotparser.RobotFileParser()
        self.parser.set_url(link)
        self.parser.read()

    def can_fetch(self, link):
        return self.parser.can_fetch("*", link)

    @classmethod
    def is_robots_content(cls, content):
        return "User-agent:" in content

