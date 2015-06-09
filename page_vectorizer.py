__author__ = 'Tomasz Truszkowski <tomtrusz@gmail.com>'

import os
import nltk
from nltk.stem.porter import PorterStemmer

class PageVectorizer:
    def __init__(self):
        self.data = {}
        self.doc_vectors = {}
        self.vocabulary = {}
        self.vocabulary_size = 0
        #self.stemmer = PorterStemmer()

    def add_document(self, name, text):
        self.data[name] = self.tokenize(text)

    # Extracts only alpha words (no numbers or punctuatuion)
    def extract_good_words(self, text):
        stopwords = nltk.corpus.stopwords.words('english')
        content = [w for w in text if w.lower() not in stopwords]
        content = [w for w in content if w.isalpha() and len(w) > 2]
        #content = [self.stemmer.stem(w) for w in content]
        return content

    def tokenize(self, text):
        words = nltk.wordpunct_tokenize(text)
        return self.extract_good_words(words)

    def make_vocabulary(self, threshold=4):
        for name, doc_words in self.data.items():
            for word in doc_words:
                if word not in self.vocabulary:
                    self.vocabulary[word] = 0
                else:
                    self.vocabulary[word] += 1

        # Prune not so frequent words
        to_remove = []
        for word, count in self.vocabulary.items():
            if count < threshold:
                to_remove.append(word)

        for word in to_remove:
            del self.vocabulary[word]

        # Assign ids to each word
        vocab_it = 0
        for word in self.vocabulary.keys():
            self.vocabulary[word] = vocab_it
            vocab_it += 1

        self.vocabulary_size = vocab_it

    def make_doc_vectors(self):
        self.make_vocabulary()
        for name, doc_words in self.data.items():
            self.doc_vectors[name] = [0] * self.vocabulary_size

            for word in doc_words:
                if word in self.vocabulary:
                    word_id = self.vocabulary[word]
                    self.doc_vectors[name][word_id] += 1
