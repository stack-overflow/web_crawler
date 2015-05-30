# Copyright (c) 2015 Tomasz Truszkowski <tomtrusz@gmail.com>
__author__ = 'Tomasz Truszkowski <tomtrusz@gmail.com>'
from html.parser import HTMLParser

class HtmlLinkExtractor(HTMLParser):
    def __init__(self, links):
        self.links = links
        super(HtmlLinkExtractor, self).__init__()

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for a in attrs:
                if a[0] == 'href':
                    self.links.append(a[1])