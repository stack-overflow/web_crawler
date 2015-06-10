#!/usr/bin/env python3
# Copyright (c) 2015 Tomasz Truszkowski <tomtrusz@gmail.com>
__author__ = 'Tomasz Truszkowski <tomtrusz@gmail.com>'

# Concurrency
import concurrent.futures
from queue import Queue
from operator import itemgetter
import time
import random

import page
import web_graph
import page_vectorizer

class LinkTraverser:
    def __init__(self, root_link):
        page.Page.set_root_url(root_link)
        self.root_page = page.Page(root_link)
        self.root_page.process()
        self.work_queue = Queue()
        self.work_queue.put(self.root_page)
        self.vectorizer = page_vectorizer.PageVectorizer()

    def visit_one_page(self, page):
        # Check page.processed to avoid calling page.process()
        # for processed pages. The page.process() also checks
        # page.processed field, but inside the locked block.
        if not page.processed:
            return page.process()
        else:
            return False

    def traverse_concurrent(self, page: page.Page):
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
                        self.vectorizer.add_document(child.link, child.normalized_text)
                    elif child.error:
                        page.children.remove(child)

        return result_children

    def go_concurrent(self):
        while not self.work_queue.empty():
            cur_page = self.work_queue.get()

            for next_page in self.traverse_concurrent(cur_page):
                self.work_queue.put(next_page)

        for next_page in self.traverse_concurrent(cur_page):
            self.work_queue.put(next_page)

def normalize(vec):
    s = sum(vec)
    for i in range(len(vec)):
        vec[i] = vec[i] * 1.0 / s
    return vec

if __name__ == "__main__":
    #wgraph_path = "graph-1433704861.gexf"
    wgraph_path = None
    link = "http://www.pg.gda.pl/~manus/"

    wgraph = None
    if not wgraph_path:
        t = LinkTraverser(link)
        start = time.time()
        t.go_concurrent()
        end = time.time()
        concurrent_time = end - start
        print("Concurrent time: {0}".format(concurrent_time))

        t.vectorizer.make_doc_vectors()

        print("Vocabulary: {0}".format(t.vectorizer.vocabulary))
        print("Document vectors: {0}".format(t.vectorizer.doc_vectors))

        web_graph.pages_to_hdd(t.root_page)
        wgraph = web_graph.pages_to_graph(t.root_page)
        web_graph.serialize_graph(wgraph)

        print("Start EM:")
        ilosc_topicow = 20

        doc_topic = {}
        topic_prob = {}
        for doc in t.vectorizer.data.keys():
            doc_topic[doc] = normalize([random.random() for i in range(ilosc_topicow)])
            topic_prob[doc] = [[0 for j in range(ilosc_topicow)] for i in range(t.vectorizer.vocabulary_size)]

        topic_word = [normalize([random.random() for i in range(t.vectorizer.vocabulary_size)]) for j in range(ilosc_topicow)]




        for it in range(0, 10):
            print("Iteration #"+str(it))
            #E step
            for doc in t.vectorizer.data.keys():
                for word in t.vectorizer.vocabulary.values():
                    prob = [0] * ilosc_topicow
                    for i in range(ilosc_topicow):
                        prob[i] = doc_topic[doc][i] * topic_word[i][word]
                    if sum(prob) == 0.0:
                        print("ZOMG ZLE SIE DZIEJE NA SWIECIE")
                    else:
                        topic_prob[doc][word] = normalize(prob)

            #M step
            #P(w|z)
            for topic in range(ilosc_topicow):
                for word in t.vectorizer.vocabulary.values():
                    prob = 0
                    for doc in t.vectorizer.data.keys():
                        count = t.vectorizer.doc_vectors[doc][word]
                        prob += count * topic_prob[doc][word][topic]
                    topic_word[topic][word] = prob
                topic_word[topic] = normalize(topic_word[topic])

            #P(z|d)
            for doc in t.vectorizer.data.keys():
                for topic in range(ilosc_topicow):
                    prob = 0
                    for word in t.vectorizer.vocabulary.values():
                        count = t.vectorizer.doc_vectors[doc][word]
                        prob += count * topic_prob[doc][word][topic]
                    doc_topic[doc][topic] = prob
                doc_topic[doc] = normalize(doc_topic[doc])

        #print
        #print("doc-topic: {0}".format(doc_topic))
        print("topic-words: ")
        for i in range(ilosc_topicow):
            print("topic"+str(i), end=": ")
            topic_id = sorted([[topic_word[i][j], j] for j in range(t.vectorizer.vocabulary_size)], key=itemgetter(0), reverse=True)
            for j in range(5):
                print(t.vectorizer.vocabulary_inv[topic_id[j][1]], end=", ")
            print()

        print("\n")
        print("doc-topics: ")
        for doc in t.vectorizer.data.keys():
            print(doc, end=": ")
            topic_id = sorted([[doc_topic[doc][j], j] for j in range(ilosc_topicow)], key=itemgetter(0), reverse=True)
            for j in range(2):
                print("topic"+str(topic_id[j][1]), end=", ")
            print()

        print("\n\n")




        t.root_page = None
        t = None
        page.Page.reset()
    else:
        wgraph = web_graph.deserialize_graph(wgraph_path)

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
