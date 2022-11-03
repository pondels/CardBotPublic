from discord import channel
from pymongo.errors import ServerSelectionTimeoutError
from cardgames.database import DatabaseQuery
from pymongo import MongoClient
from datetime import datetime
import random
import os

class CardJitsu():

    def __init__(self, token, databaseQuery):
        self.databaseQuery = databaseQuery
        self.cluster = MongoClient(token)
        self.clubpenguincards = {}

        self.images = {
            0: {
                'b': './images/colorElements/bluefire.png',
                'g': './images/colorElements/greenfire.png',
                'o': './images/colorElements/orangefire.png',
                'y': './images/colorElements/yellowfire.png',
                'p': './images/colorElements/purplefire.png',
                'r': './images/colorElements/redfire.png'
            },
            1: {
                'b': './images/colorElements/bluewater.png',
                'g': './images/colorElements/greenwater.png',
                'o': './images/colorElements/orangewater.png',
                'y': './images/colorElements/yellowwater.png',
                'p': './images/colorElements/purplewater.png',
                'r': './images/colorElements/redwater.png'
            },
            2: {
                'b': './images/colorElements/bluesnow.png',
                'g': './images/colorElements/greensnow.png',
                'o': './images/colorElements/orangesnow.png',
                'y': './images/colorElements/yellowsnow.png',
                'p': './images/colorElements/purplesnow.png',
                'r': './images/colorElements/redsnow.png'
            },
        }

        filename = './cardgames/cards/clubpenguincards'
        files = os.listdir(filename)
        for file in files:
            index = file.split('_')[-1].split('.')[0]
            self.clubpenguincards[index] = f'{filename}/{file}'

    def getDeck(self, ctx):
        '''
            Grabs a user's deck information. If they don't
            have any deck information, give them a base
            deck to have. 
        '''
        try:
            db = self.cluster['player-info']
            collection = db['users']
            users = collection.find()
            for user in users:
                if user['_id'] == ctx:
                    return user['deck']
            return "Nothing Found!"
        except ServerSelectionTimeoutError:
            return "Could Not Connect to Server.\nPlease Try again shortly!" 

    def openPack(self, ctx, packNumber):
        '''
            Gather's the user's deck
            and opens a pack for a certain
            currency from a specific series (packNumber),
            giving them more cards in their deck to use.
        '''
        cardsUnpacked = "Couldn't connect you to database!\nPlease wait a while longer and try again!"
        if packNumber < 9 and packNumber > 0:
            cardsUnpacked = self.databaseQuery.openCardJitsuPack(ctx, packNumber)

        return cardsUnpacked

    def createGame(self, interaction, username, channel_id):
        '''
            Creates a "game" code in the database that has a set amount of people that
            can join, so that could be the "server" that players can play in.
        '''
        
        started = self.databaseQuery.startGame(interaction, username, channel_id, "CPJ", 2)
        return started

    def dealHands(self, player, gameCollection):
        # Initializing an array of the user's deck
        userDB = self.cluster['player-info']
        userDecks = userDB['users']
        decks = userDecks.find()
        playersCards = []

        for user in decks:
            if user['_id'] == player['_id']:
                for data in user['deck']:
                    playersCards.append(data)
                break
        
        gameCollection.update_one({'_id': player['_id']}, {'$set': {'hand': [random.choice(playersCards) for _ in range(5)]}})
    
    def takeTurn(self, username, cardNumber):
        '''
            Triggered when a player chooses a card, they trigger
            the takeTurn function and it plays their card they chose
            and then proceeds to draw a new card to their hand.
        
            returns message: String
                    players: List of players in game
        '''
        # Stationary Data for if no servers exist
        players, player, gameCollection = self.databaseQuery.player_lookup(username)

        if not player['turn_taken']: # They haven't taken their turn yet
            hand = player['hand']
            card = hand[cardNumber - 1] # Card chosen
            gameCollection.update_one({"_id": username}, {"$set": {'card_information': card}}) # Updates this to the card they chose

            # Grabbing user's deck
            playerDB = self.cluster['player-info']
            playerCollections = playerDB['users']
            players = playerCollections.find()

            for player in players:
                if player['_id'] == username:
                    new_card = random.choice(player['deck'])
                    hand.pop(cardNumber - 1)
                    hand.insert(cardNumber - 1, new_card)
                    gameCollection.update_one({"_id": username}, {"$set": {'hand': hand}})
                    gameCollection.update_one({"_id": username}, {"$set": {'turn_taken': True}})
                    break
        
        players, _, _ = self.databaseQuery.player_lookup(username)
        return players

    def showHand(self, username):
        '''
            Sends the hand of a player to a given channel
        '''
        hand = ''
        _, player, _ = self.databaseQuery.player_lookup(username)
        
        for card in player['hand']:
            hand += card['card_image']
        
        return hand

    def check_elements(self, players):
        '''
            Checks the information on the cards
            and determines if a win was made

            returns winner's username or None
        '''
        elements = []
        for player_info in players:
            # Add the players elements to the elements grid
            elements.append(player_info[1]['element'])

        if (elements[0] == 'f' and elements[1] == 's') or (elements[0] == 's' and elements[1] == 'f'):
            # Fire Beats Snow
            if elements[0] == 'f': winner, loser = players[0][0], players[1][0]
            else: winner, loser = players[1][0], players[0][0]
        elif (elements[0] == 'f' and elements[1] == 'w') or (elements[0] == 'w' and elements[1] == 'f'):
            # Water Beats Fire
            if elements[0] == 'w': winner, loser = players[0][0], players[1][0]
            else: winner, loser = players[1][0], players[0][0]
        elif (elements[0] == 'w' and elements[1] == 's') or (elements[0] == 's' and elements[1] == 'w'):
            # Snow Beats Water
            if elements[0] == 's': winner, loser = players[0][0], players[1][0]
            else: winner, loser = players[1][0], players[0][0]
        else:
            # The Elements are equal to eachother so returns None
            return None, None
        return winner, loser

    def check_value(self, players):
        '''
            Checks the value of the card and determines
            a winner based on that

            returns: Username = name of the player who won
        '''
        card_values = []
        for player_info in players:
            # Add the players elements to the elements grid
            card_values.append(int(player_info[1]['value']))
        if card_values[0] < card_values[1]:
            winner, loser = players[1][0], players[0][0]
        elif card_values[0] > card_values[1]:
            winner, loser = players[0][0], players[1][0]
        else:
            return None, None
        return winner, loser

    def winningCard(self, username):
        '''
            go through all the databases and check if
            both players have submitted a card

            From the two cards it will check which card
            beats which and place the winning card in it's
            according data structure for the user

            Resets data that needs resetting at the end
        '''
        people, _, gameCollection = self.databaseQuery.player_lookup(username)
        
        players = []

        for player in people:
            username = player['_id']
            card_information = player['card_information']
            if card_information != {}:
                players.append([username, card_information])
                
        # Check if a player won via elements
        who_won, who_lost = self.check_elements(players)
        # Runs if they both chose the same element
        if who_won == None:
            # Checks if the player won via card value
            who_won, who_lost = self.check_value(players)
            # Runs if they both chose the same card value
            if who_won == None:
                gameCollection.update_one({"_id": who_won}, {"$set": {'card_information': {}}})
                gameCollection.update_one({"_id": who_lost}, {"$set": {'card_information': {}}})

        if who_won != None:
            element = ''
            color = ''
            fire = []
            water = []
            snow = []
            
            for player in people:
                if player['_id'] == who_won:
                    element = player['card_information']['element']
                    color = player['card_information']['color']
                    fire = player['fire']
                    water = player['water']
                    snow = player['snow']

            # Winner's card info updated and elements as well
            if element == 'f':
                fire.append(color)
                gameCollection.update_one({"_id": who_won}, {"$set": {'fire': fire }})

            elif element == 'w':
                water.append(color)
                gameCollection.update_one({"_id": who_won}, {"$set": {'water': water }})

            else:
                snow.append(color)
                gameCollection.update_one({"_id": who_won}, {"$set": {'snow': snow }})

            # Winner's Previous chosen card is set to empty
            gameCollection.update_one({"_id": who_won}, {"$set": {'card_information':{}}})

            # Reset's their turn
            gameCollection.update_one({"_id": who_won}, {"$set": {'turn_taken': False }})

            # Loser's card_info updated to nothing since they didn't win
            gameCollection.update_one({"_id": who_lost}, {"$set": {'card_information':{}}})

            # Reset's their turn
            gameCollection.update_one({"_id": who_lost}, {"$set": {'turn_taken': False }})

        return who_won, who_lost

    def pay_players(self, winner, loser):
        '''
            Goes through all the servers and checks to see
            a user won the game.

            If the user won the game, they win some credits.
            The loser gains participation credits too.

            When someone wins and all of their money is awarded
            the server is dropped / deleted

            returns: winnerFound = Boolean
                     message = None // Only if no one won. Is overridden by cardwinner
                     message = Which user won and how they won.
        '''

        winning_reward = 625
        participation_reward = 125

        # Update Winner's and loser's balance and drop the game from the database
        userDB = self.cluster['player-info']
        userCollections = userDB['users']
        users = userCollections.find()
        for user in users:
            if user['_id'] == winner:
                userCollections.update_one({"_id": winner}, {"$set": {'balance': user['balance'] + winning_reward}})
            elif user['_id'] == loser:
                userCollections.update_one({"_id": loser}, {"$set": {'balance': user['balance'] + participation_reward}})

    def overall_winner(self, username):
        # Returns True or False if a winner overall was found
        players, _, _ = self.databaseQuery.player_lookup(username)

        # Can win by 3 unique fire, water, and snow 
        # Winning by 3 unique of the same element

        for player in players:
            
            # Wins by unique Elements
            fire = list(set(player['fire']))
            water = list(set(player['water']))
            snow = list(set(player['snow']))

            if len(fire) == 3 or len(snow) == 3 or len(water) == 3:
                return True

            # Wins by unique cards across the board
            for f in fire:
                for w in water:
                    for s in snow:
                        if f != w and w != s and f != s:
                            return True

        # Nobody won that game
        return False