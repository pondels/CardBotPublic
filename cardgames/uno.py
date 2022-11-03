from cardgames.database import DatabaseQuery
import random

class Uno():

    def __init__(self, databasequery):
        self.databaseQuery = databasequery

    def can_start(self, username):
        _, player, _ = self.databaseQuery.player_lookup(username)
        if player['hand'] == []:
            return True
        return False

    def setup(self, username):
        # TODO Players cannot join once the game has started
        validate = self.checkStart(username)
        if validate:
            pile = self.createHands(username)
            return "The Game Has Successfully Begun!", pile
        else:
            return "Sorry! There are not enough players or you did not create the game!", None

    def createHands(self, username):
        unoCardsDB = self.databaseQuery.cluster['Uno-Cards']
        unoCardsCollection = unoCardsDB['unoCards']
        unoCards = unoCardsCollection.find()

        cards = []
        for card in unoCards:
            cards.append(card)

        players, player, gameCollection = self.databaseQuery.player_lookup(username)
        
        while True:
            pile = random.choice(cards)
            if self.valid_pile(pile): break

        for player in players:
            newHand = []
            # Gives the player 7 random cards
            for i in range(7):
                newHand.append(random.choice(cards))
            
            if player['party_leader']: gameCollection.update_one({'_id': player['_id']}, {"$set": {'pile': pile}})
            gameCollection.update_one({'_id': player['_id']}, {"$set": {'hand': newHand}})
        
        return pile

    def valid_pile(self, pile):
        if pile['type'] == 'wild' or pile['type'] == 'plusfour':
            return False
        return True

    def checkStart(self, username):

        players, player, _ = self.databaseQuery.player_lookup(username)
        isLeader = player['party_leader']
        
        if len(players) >= 2 and isLeader: return True    
        return False
    
    def draw_card(self, username):
        # Ignore valid card to use
        # If draw is forced
        unoCardsDB = self.databaseQuery.cluster['Uno-Cards']
        unoCardsCollection = unoCardsDB['unoCards']
        unoCards = unoCardsCollection.find()

        cards = []
        for card in unoCards:
            cards.append(card)

        _, player, gameCollection = self.databaseQuery.player_lookup(username)


        newHand = player['hand']
        card = random.choice(cards)
        newHand.append(card)
        gameCollection.update_one({'_id': player['_id']}, {"$set": {'hand': newHand}})

        if player['uno']:
            gameCollection.update_one({'_id': player['_id']}, {"$set": {'uno': False}})
        return card["image"], player['channel_id']

    def pass_turn(self, username):
        # returns the next players channel, and username

        players, player, gameCollection = self.databaseQuery.player_lookup(username)

        for player in range(len(players)):
            if players[player]['is_turn']:
                gameCollection.update_one({'_id': players[player]['_id']}, {"$set": {'is_turn': False}})
                if player == len(players) - 1:
                    gameCollection.update_one({'_id': players[0]['_id']}, {"$set": {'is_turn': True}})
                    return players[0]['channel_id'], players[0]['_id']
                else:
                    gameCollection.update_one({'_id': players[player+1]['_id']}, {"$set": {'is_turn': True}})
                    return players[player+1]['channel_id'], players[player+1]['_id']

    def reverse(self, username):
        # Reverses all the players in the game.
        players, _, gameCollection = self.databaseQuery.player_lookup(username)

        last_index = len(players) - 1
        inverted_game = [players[last_index - n] for n in range(len(players))]

        key = gameCollection.name
        gameCollection.drop()

        gameDB = self.databaseQuery.cluster['servers']
        gameCollection = gameDB[key]

        for player in inverted_game:
            gameCollection.insert_one(player)

    def showHand(self, username):
        # Returns the channel, and Formatted hand (All Images)

        _, player, _ = self.databaseQuery.player_lookup(username)

        return player['channel_id'], player['hand']

    def show_starting_hands(self, username):

        players, player, _ = self.databaseQuery.player_lookup(username)

        channels_and_cards = []

        for player in players:
            formattedHand = ''
            for card in player['hand']:
                formattedHand += card['image'] + " "

            channels_and_cards.append([player['channel_id'], formattedHand])

        return channels_and_cards

    def is_turn(self, username):
        # Returns True or False if it is the players turn
        # Returns channel to await to player
        _, player, _ = self.databaseQuery.player_lookup(username)
        if player['is_turn']:
            return True, player['channel_id']
        
        return False, player['channel_id']

    def check_valid_card(self, username, n, color=None):
        # Returns
        #   Bool
        #   Card as dict object
        #   List of Players
        
        players, player, gameCollection = self.databaseQuery.player_lookup(username)

        hand = player['hand']

        leader = self.find_leader(players)

        if len(hand) >= n:
            card = hand[n-1]
            pile = leader['pile']
            if card['type'] == pile['type'] or card['color'] == pile['color'] or card['type'] == 'wild' or card['type'] == 'plusfour':
                if card['type'] == 'wild' or card['type'] == 'plusfour':
                    if color == None:
                        return False, None, None
                    else:
                        colors = ['yellow', 'green', 'blue', 'red']
                        if color.lower() in colors:
                            hand.remove(card)
                            card['color'] = color
                            gameCollection.update_one({'_id': leader['_id']}, {"$set": {'pile': card}})
                            for player in players:
                                if player['_id'] == username:
                                    gameCollection.update_one({'_id': player['_id']}, {"$set": {'hand': hand}})
                                    break
                            return True, card, players
                        else:
                            return False, None, None
                else:
                    hand.remove(card)
                    gameCollection.update_one({'_id': leader['_id']}, {"$set": {'pile': card}})
                    for player in players:
                        if player['_id'] == username:
                            gameCollection.update_one({'_id': player['_id']}, {"$set": {'hand': hand}})
                            break
                    return True, card, players
            else: return False, None, None
        else: return False, None, None

    def find_leader(self, players):
        # Finds the leader of the party   
        for player in players:
            if player['party_leader']:
                return player

    def check_uno(self, username):
        # Returns True if they have 1 card but DIDNT call uno

        _, player, _ = self.databaseQuery.player_lookup(username)

        if len(player['hand']) == 1:
            return True
        return False

    def check_win(self, username):
        _, player, _ = self.databaseQuery.player_lookup(username)
        if player['hand'] == []:
            return True
        return False

    def callout(self, username):
        # Runs when a player thinks a player has 1 card in their hand.
        players, _, gameCollection = self.databaseQuery.player_lookup(username)
        
        for player in players:
            if len(player['hand']) == 1 and not player['uno']:
                if player['_id'] == username:
                    gameCollection.update_one({'_id': username}, {'$set': {'uno': True}})
                    return 'safe', None
                else:
                    cards = []
                    for _ in range(2):
                        card, channel = self.draw_card(player['_id'])
                        cards.append(card)
                    return cards, channel
        return 'No valid player found to call uno!', None