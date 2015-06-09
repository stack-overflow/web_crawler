from html.parser import HTMLParser


class HtmlTextExtractor(HTMLParser):
    def __init__(self):
        self.text = ""
        super(HtmlTextExtractor, self).__init__()

    def handle_data(self, data):
        self.text += data.strip()

    def handle_starttag(self, tag, attrs):
        self.text += " "