from pymongo import MongoClient

class BlackJack():

    def __init__(self, token):
        self.cluster = MongoClient(token)

    def showHand(self, ctx):
        '''
            Shows the player's current hand
        '''
        pass

    def hit(self, ctx):
        '''
            Adds another card from a deck 
            registered to a specific player
            and adds the number to their total
        '''
        pass

    def findTotal(self, ctx):
        '''
            Returns the total value(s) of a
            player's hand.
        '''
        pass

    def turnDone(self, ctx):
        '''
            Ran when the player declares when
            they are done hitting.
        '''
        pass

    def checkBust(self, ctx):
        '''
            Determines whether or not a player
            busted on their hand.
        '''
        pass

    def newHand(self, ctx):
        '''
            Runs if the player started a fresh
            game and deals them a new hand.
        '''
        pass

    def splitHand(self, ctx):
        '''
            Splits the hand of the player into 
            2 piles if they have enough money,
            they only have 2 cards in their hand,
            and both cards are of same value.
        '''
        pass

    def doubleDown(self, ctx):
        '''
            Places a card face down on the player's 
            current hand and passes it over to the dealer.
            
            This double's the player's bid and splits it evenly
            into both hands
        '''
        pass

    def checkBlackjack(self, ctx):
        '''
            Runs once the player is dealt a new hand and
            checks if the value of their hand is equal to 21.

            Returns True or False
        '''
        pass

    def checkWin(self, ctx):
        '''
            Runs when the dealer is finished playing.

            This returns an Enum of 3 items.
            - Win, Lose, Tie

            Returns for type in changeFunds
            win = add
            lose = subtract
            tie = add (returns funds once complete)
        '''
        pass

    def changeFunds(self, ctx, bid, type):
        '''
            Runs once when the game starts, and once when the game
            ends

            bid = Initial bid of player

            type = Add or Subtract $$$ from account
        '''
        pass

    def insurance(self, ctx):
        '''
            Prompts the user for insurance to place extra
            money in the pot in case the dealer got
            a blackjack.
        '''
        pass