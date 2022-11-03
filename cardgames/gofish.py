from pymongo import MongoClient

class GoFish:

    def __init__(self, token):
        self.cluster = MongoClient(token)