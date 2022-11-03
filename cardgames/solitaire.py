from pymongo import MongoClient

class Solitaire:

    def __init__(self, token):
        self.cluster = MongoClient(token)