from pymongo import MongoClient
import random
from datetime import datetime, timedelta
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError

# This is a file to manage basic data queries for users

class DatabaseQuery():

    def __init__(self, token):
        try:
            self.cluster = MongoClient(token)
            self.starterDeck = ["1","3","6","9","13","14","15","17","18","20","22","23","26","29","73","81","89","90","202","204","216","218","220","222","229","250","303","304","305","312","314","319","352"]
            self.letters = [chr(s) for s in range(65, 91)] + [chr(i) for i in range(97, 123)]
            self.numbers = [i for i in range(10)]
        except ServerSelectionTimeoutError:pass
            

    def abandonMatch(self, username, force=None):
        '''
            This is ran when a user concedes to a
            Match, they automatically lose and don't
            make any money this way from playing :(
        '''
        gameDB = self.cluster['servers']
        for collection in gameDB.list_collection_names():
            gameCollection = gameDB[collection]
            games = gameCollection.find()

            users = 0
            for _ in games:
                users += 1

            gameCollection = gameDB[collection]
            games = gameCollection.find()

            for player in games:
                if player["_id"] == username:
                    if users == 1 or player['party_leader'] or force == True: gameCollection.drop()
                    else: gameCollection.delete_one({'_id': username})
                    return "You Conceded!"

        return "You are not in a game!"

    def balanceChecker(self, ctx):
        nameDB = self.cluster['player-info']
        userInfo = nameDB['users']
        users = userInfo.find()

        for user in users:
            if user["_id"] == ctx:
                return user["balance"]

    def collect(self, username, set, collectED):
        # Deck database
        userDB = self.cluster['player-info']
        userDecks = userDB['users']
        decks = userDecks.find()

        set_cards = []
        players_cards = []

        # All user's cards in the given set
        for user in decks:
            if user['_id'] == username:
                for card in user['deck']:
                    if card['set_id'] == set:
                        players_cards.append(card)
        
        # Card database
        cardDB = self.cluster['card-jitsu']
        cardCollection = cardDB['cards']
        cards = cardCollection.find()

        # All cards in the given set
        for card in cards:
            if card['set_id'] == set:
                set_cards.append(card)

        if len(set_cards) - len(players_cards) == 0: return f'You have collected everything from set {set}!'
        if collectED == 'collect':
            return f'You need to collect {len(set_cards) - len(players_cards)} more card(s) in set {set}!'
        return f'You have collected {len(players_cards)} out of {len(set_cards)} cards in set {set}!'

    def dailyClaim(self, ctx):

        daily = [250, 275, 300, 325]
        
        return self.xClaim(daily, ctx, 'daily')

    def game_started(self, key):

        # Returns True if the game has started
        gameDB = self.cluster['servers']
        gameCollection = gameDB[key]
        players = gameCollection.find()

        for player in players:

            # Hands are dealt once the game starts
            #   So it's started if they have cards
            if player['hand'] != []:
                return True

        return False

    def get_lobby(self, key):
        # Returns a list of players in the lobby
        gameDB = self.cluster['servers']
        gameCollection = gameDB[key]
        games = gameCollection.find()
        players = []

        for player in games:
            players.append(player)

        return players, gameCollection

    def get_msg_id(self, username):
        _, player, _ = self.player_lookup(username)
        return player['message_id']

    def joinGame(self, interaction, username, key, channel_id):
        interaction = str(interaction)
        '''
        Searches for a game with a given key and
        lets them in if there's a spot open
        '''
        try:
            _, player, _ = self.player_lookup(username)
            if player != None: return 'You are already in a game!'

            players, gameCollection = self.get_lobby(key)

        # Runs if the database isn't being connected to for some reason
        except ServerSelectionTimeoutError:
            return "Could Not Connect to Server.\nPlease Try again shortly!"
        except:
            return "External Problem"

        if players != []:
            if 0 < len(players) and len(players) < int(key[3:4]):
                if key[:3] == 'CPJ':
                    gameCollection.insert_one({"_id": username, "ctx": interaction, "party_leader": False, "hand": [], "fire": [], "water": [], "snow": [], "turn_taken": False, "won_move": False, "card_information": {}, 'channel_id': channel_id})

                elif key[:3] == 'UNO':
                    gameCollection.insert_one({"_id": username, "ctx": interaction, "party_leader": False, "is_turn": False, 'hand': [], 'uno': False, 'channel_id': channel_id})
                
                return "Successfully Connected To Server!"
            
            elif len(players) >= int(key[3:4]):
                return "Server is full!"
        
        return "Server Does Not Exist!"

    def monthlyClaim(self, ctx):

        monthly = [8000, 8500, 9000, 9500, 10000]

        return self.xClaim(monthly, ctx, 'monthly')

    def openCardJitsuPack(self, ctx, num):
        pack_string = self.openPack(num, ctx)
        return pack_string

    def openPack(self, packNumber, ctx):
        '''
            Opens 7 random cards from a given pack of cards
        '''
        # All of the users in the database
        userDB = self.cluster['player-info']
        userBalances = userDB['users']
        users = userBalances.find()

        for user in users:
            if user["_id"] == ctx:
                if user['balance'] < 1500:
                    return "You Need 1500 Gold To Open Up A Pack!"
                else:
                    userBalances.update_one({"_id": ctx}, {"$set": {'balance': user['balance'] - 1500}})

        users = userBalances.find()

        # Finding user's deck information
        playersCards = []
        for user in users:
            if user['_id'] == ctx:
                for card in user['deck']:
                    playersCards.append(card)

        # All the cards in the game
        cardDB = self.cluster['card-jitsu']
        cardCollection = cardDB['cards']
        cards = cardCollection.find()

        # Adds all cards to a set
        allCards = []
        for card in cards:
            if card['set_id'] == str(packNumber):
                allCards.append(card)
        
        # Generates 7 random cards; packGenerator gets the emoji, addToUserDeck gets the dictionary
        packGenerator = ''
        addToUserDeck = []
        for i in range(7):
            randomlyChosenCard = random.choice(allCards)
            packGenerator += randomlyChosenCard['card_image']
            addToUserDeck.append(randomlyChosenCard)

        # Writes the new cards into the players current deck
        userDB = self.cluster['player-info']
        userDecks = userDB['users']
        users = userDecks.find()
        for user in users:
            if user["_id"] == ctx:
                for i in range(len(addToUserDeck)):
                    if addToUserDeck[i] not in playersCards:
                        playersCards.append(addToUserDeck[i])
                userDecks.update_one({"_id": ctx}, {"$set": {'deck': playersCards}})
        
        return packGenerator

    def player_lookup(self, username):
        # returns a list of players
        #   the player to find
        #   the dataCollection
        isFound = False
        gameDB = self.cluster['servers']
        for collection in gameDB.list_collection_names():
            gameCollection = gameDB[collection]
            games = gameCollection.find()
            players = []
            count = 0
            for player in games:
                players.append(player)
                if player['_id'] == username:
                    isFound = True
                    playerToFind = players[count]
                count += 1
            if isFound: break

        if not isFound: return None, None, None
        return players, playerToFind, gameCollection

    def send_report(self, report, username):
        reportDB = self.cluster['Reports']
        reportCollection = reportDB['reports']
        reports = reportCollection.find()

        count = 0
        for _ in reports:
            count += 1

        reportCollection.insert_one({'_id': count, 'username': username, 'report': report})

    def send_suggestion(self, report, username):
        suggestionDB = self.cluster['Suggestions']
        suggestionsCollection = suggestionDB['suggestions']
        suggestions = suggestionsCollection.find()

        count = 0
        for _ in suggestions:
            count += 1

        suggestionsCollection.insert_one({'_id': count, 'username': username, 'suggestion': report})

    def setup(self, ctx):
        '''
            Checks if the user is in the database
            If not in the database, sets them up
            with some cards. Otherwise returns
            True. (in the system)
        '''
        # All of the users in the database
        userDB = self.cluster['player-info']
        userCollection = userDB['users']
        users = userCollection.find()
        
        for user in users:
            if user['_id'] == ctx:
                return "You're already in The System!"

        # All of the cards in the database
        cardDB = self.cluster['card-jitsu']
        cardCollection = cardDB['cards']
        cards = cardCollection.find()

        # Finds Card information
        deckArrangement = []

        for card in cards:
            if card['_id'] in self.starterDeck:
                deckArrangement.append(card)

        post = {'_id': ctx, 'balance': 0, 'daily': 0, 'weekly': 0, 'monthly': 0, 'deck': deckArrangement}
        userCollection.insert_one(post)
        return "You've successfully been added to the system!"

    def showGames(self):
        # Games returns the Code and the Player(s) inside
        
        allGames = []

        # Iterates through all of the games 
        gameDB = self.cluster['servers']
        count = 0
        for collection in gameDB.list_collection_names():
            allGames.append({collection: []})
            gameCollection = gameDB[collection]
            games = gameCollection.find()

            # Checks how many players are in the game and adds them to the string
            for player in games:
                allGames[count][collection].append(player["_id"])
            count += 1
        if allGames == '': return "No Games Found!"
        return allGames

    def startGame(self, interaction, username, channel_id, game_type, max_players):
        interaction = str(interaction)
        '''
        Creates a game with a key that 2 people can be in
        '''
        # Only lets the user start the game if they
        # are not currently in one.

        # Generates a random server key
        generatedKey = f'{game_type}{max_players}-'
        for _ in range(7):
            # Letters have 2/3 Chance
            # Numbers have 1/3 Chance
            list_choice = random.choice([self.letters, self.letters, self.numbers])
            item_chosen = random.choice(list_choice)
            generatedKey += str(item_chosen)

        # For now it will just generate a game
        try:
            # Initiating New Game
            gameDB = self.cluster['servers']
            gameCollection = gameDB[generatedKey]
            games = gameCollection.find()

            for collection in gameDB.list_collection_names():
                gamesCollections = gameDB[collection]
                games = gamesCollections.find()
                for player in games:
                    if player["_id"] == username:
                        return "You Are Already In A Game!"

            if generatedKey[:3] == 'CPJ':

                # Initializing an array of the user's deck
                userDB = self.cluster['player-info']
                userDecks = userDB['users']
                decks = userDecks.find()
                playersCards = []

                for i in decks:
                    if i['_id'] == username:
                        for data in i['deck']:
                            playersCards.append(data)
                
                gameCollection.insert_one({"_id": username, "ctx": interaction, "party_leader": True, "hand": [], "fire": [], "water": [], "snow": [], "turn_taken": False, "won_move": False, "card_information": {}, 'channel_id': channel_id})
        
            elif generatedKey[:3] == 'UNO':
                gameCollection.insert_one({"_id": username, "ctx": interaction, "party_leader": True, "is_turn": True, 'hand': [], "pile": {}, 'uno': False, 'channel_id': channel_id})

        except ServerSelectionTimeoutError: return "Could Not Connect to Server.\nPlease Try again shortly!"
        return f"Game Started! Your Game Code Is: {generatedKey}"

    def weeklyClaim(self, ctx):

        weekly = [2000, 2250, 2500, 2750, 3000]
        
        return self.xClaim(weekly, ctx, 'weekly')
    
    def xClaim(self, rewards, ctx, time):
        '''
            Adaptively update the x claim functions

            rewards = array of random rewards for the given time
            ctx = username of the user who ran the command
            time = string of which function was ran
        '''
        nameDB = self.cluster['player-info']
        userInfo = nameDB['users']
        users = userInfo.find()

        rewardChoice = random.choice(rewards)

        for user in users:
            if user["_id"] == ctx:
                if user[time] == 0:
                    userInfo.update_one({"_id": ctx}, {"$set": {'balance': user['balance'] + rewardChoice}}) # Updates the Balance of the User
                    userInfo.update_one({"_id": ctx}, {"$set": {time: datetime.now()}}) # Updates the Daily Timer
                    return f"+{rewardChoice}$ Your New Balance: ${user['balance'] + rewardChoice}" # Returns a string formatted balance to the user
                else:
                    datetimeObject =  datetime.now() - user[time]
                    days, hours, minutes = datetimeObject.days, datetimeObject.seconds//3600, (datetimeObject.seconds//60)%60
                    if time == 'monthly':
                        days_left = 30 - days
                        verify = 'month'
                    elif time == 'weekly':
                        days_left = 6 - days
                        verify = 'week'
                    else:
                        days_left = 0
                        verify = 'day'
                    hours_left = 23 - hours
                    minutes_left = 59 - minutes
                    if (days >= 1 and verify == 'day') or (days >= 7 and verify == 'week') or (days >= 31 and verify == 'month'):
                        userInfo.update_one({"_id": ctx}, {"$set": {'balance': user['balance'] + rewardChoice}}) # Updates the Balance of the User
                        userInfo.update_one({"_id": ctx}, {"$set": {time: datetime.now()}}) # Updates the x Timer
                        return f"+{rewardChoice}$ Your New Balance: ${user['balance'] + rewardChoice}" # Returns a string formatted balance to the user
                    return f"Sorry! Looks like it hasn't quite been a {verify} yet!\nCome back in {days_left} days, {hours_left} hours and {minutes_left} minutes!"
        return "Whoops! Looks like you're not showing up in our system!\nPlease use '/setup' to be registered in our system!"

    def valid_server(self, key):
        # Returns True if the server exists
        players, _ = self.get_lobby(key)
        if players != []: return True
        return False