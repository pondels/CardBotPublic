from dotenv.main import load_dotenv
import discord
from discord import app_commands
import os
from datetime import datetime
from cardgames.database import DatabaseQuery
from cardgames.cardjitsu import CardJitsu
from cardgames.uno.uno import Uno
from cardgames.gofish import GoFish
from cardgames.blackjack import BlackJack
from cardgames.solitaire import Solitaire
from typing import Literal
from PIL import Image, ImageDraw, ImageFont
# from discord import FFmpegPCMAudio
# import random
# import asyncio

load_dotenv()
TOKEN = os.getenv('TOKEN')
database = os.getenv('MONGO_TOKEN')

# Initializing Games
databasequery = DatabaseQuery(database)

cardjitsuHandler = CardJitsu(database, databasequery)
unoHandler = Uno(databasequery)
blackjackHandler = BlackJack(database)
gofishHandler = GoFish(database)
solitaireHandler = Solitaire(database)

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
guilds = discord.Object(id=989412607335227402)

bot_start_time = datetime.now()
guilds = discord.Object(id=989412607335227402)

# Stores everyone's interaction for sending/editing messages
    # i.e. {'mathidiot', {'interaction': <discord.Interaction> object}, 'view': <discord.ui.View> object}
interaction_objects = {}

@tree.command(name='help', description='A command for help on other commands!')
async def _help(interaction):
    username = interaction.user.name
    channel = await interaction.user.create_dm()
    embed=discord.Embed(
        title="Here's a Help Bar For The Bot!",
        description="Click [Here](https://mathbotinc.glitch.me/) for a guide to the bot!\n\n" + \
        '**GAMES**\n' + \
        'Apples To Apples     🍎\n' + \
        'Baccarat             🎰\n' + \
        'BlackJack            🎲\n' + \
        'Card-Jitsu           🪨📜✂️\n' + \
        'Chess                 ♟️\n' + \
        'Exploding Kittens    🐱\n' + \
        'GoFish               🐟\n' + \
        'Minesweeper          💣\n' + \
        'Oasis Poker          🎰\n' + \
        'Solitaire            🃏\n' + \
        'Texas Holdem         ♠️\n' + \
        'Three Card Poker     🎰\n' + \
        'Uno                  🔄\n\n' + \
        '**OTHER COMMANDS**\n' + \
        'Abandon              ⛔\n' + \
        'Balance              💳\n' + \
        'Daily/Weekly/Monthly 💵\n' + \
        'Games                🕹️\n' + \
        'Join                 🔑\n' + \
        'Lobby                👥\n' + \
        'Report               ⚠️\n' + \
        'Rules                📋\n' + \
        'Setup                💾\n' + \
        'Suggestion           ✅' ,
        color=0xFF5733)
    await channel.send(embed=embed)
    await interaction.response.send_message(f'Help Instructions Have Been Messaged To You Directly, {username}!')

@tree.command(name="balance", description="A Command to View Your Balance!")
async def _balance(interaction):
    balance = databasequery.balanceChecker(interaction.user.name)
    await interaction.response.send_message(f"You Currently Have ${balance}.00")

@tree.command(name="daily", description="A Command to View Your Balance!")
async def _daily(interaction):
    daily_claim = databasequery.dailyClaim(interaction.user.name)
    await interaction.response.send_message(daily_claim)

@tree.command(name="weekly", description="A Command to View Your Balance!")
async def _weekly(interaction):
    weekly_claim = databasequery.weeklyClaim(interaction.user.name)
    await interaction.response.send_message(weekly_claim)

@tree.command(name="monthly", description="A Command to View Your Balance!")
async def _monthly(interaction):
    monthly_claim = databasequery.monthlyClaim(interaction.user.name)
    await interaction.response.send_message(monthly_claim)

@tree.command(name='setup', description='Sets the player up in the database.')
async def _setup(interaction):
    '''
        Checks if the player is in
        the database, if not, sets them up with 
        literally everything.

        Otherwise, cancels the command.
    '''
    response = databasequery.setup(interaction.user.name)
    role = discord.utils.get(interaction.user.guild.roles, name = "Member")
    await interaction.user.add_roles(role)
    await interaction.response.send_message(response)

@app_commands.describe(
    type = 'The argument to choose.',
    player_count = 'Numbers of players to limit in game. (1 - )'
)
@app_commands.choices(type = [
    app_commands.Choice(name = 'Create A Game (Requires Player Count Option)',           value = ''),
    app_commands.Choice(name = 'Start The Game',                                         value = ''),
    app_commands.Choice(name = 'Spectate (Spectate Without Playing Game)',               value = ''),
    app_commands.Choice(name = 'Play (Jump Back In Game If Spectating)',                 value = ''),
    app_commands.Choice(name = 'Bid  (Typically Done When the Game Starts)',             value = ''),
    app_commands.Choice(name = 'Insurance (Done to save money if dealer has BlackJack)', value = ''),
    app_commands.Choice(name = 'Hit  (Add another card)',                                value = ''),
    app_commands.Choice(name = 'Pass (End your turn for that hand)',                     value = ''),
    app_commands.Choice(name = 'Split (Split hand in 2 piles if cards are the same)',    value = ''),
    app_commands.Choice(name = 'Double Down (Add 1 last card, double your bid)',         value = '')
],
player_count = [
    app_commands.Choice(name = '1 Player', value = 1),
])
@tree.command(name="blackjack", description="Play a game of BlackJack by yourself or friends!")
async def _blackjack(interaction, type: app_commands.Choice[str], player_count: app_commands.Choice[int] = None):
    '''

        Players are given 15 seconds to make a bid
            If they run out of time, they are automatically placed as a spectator for the game

        Every player makes a bid
        If a player doesn't want to play that round, they may choose to spectate.
            The player can join back in at any time.
            If a player joins after bids are made, they can't play until a new game starts.
        Cards are dealt.

        If the Dealer has an Ace showing, everyone is prompted if they want insurance.
            If dealer didn't have blackjack, all insurance is taken
            If dealer did have blackjack, everyone keeps their bids and insurance IF they paid insurance.
                If they didn't pay insurance, they lose their bids. *doi*
                This top rule only applies if the player DIDNT also have a blackjack
        
        Goes around the table with dealer being last

        If Player split their hand:
            Make 2 piles and have them double their bid, split amongst the hands.

        If Player doubles down on their hand.
            Player doubles their bid
            Place card face down sideways. Their turn ends

        After all players have passed and it is the dealers turn, the dealer hits until their hand is >= 17
            If dealer busts, players win their bids
            If dealer doesn't bust:
                Players that had a lower hand count, lost their bid.
                Players that had a higher hand count win their bids.
                Players with blackjack get 2.5x their winnings.
                    Ex; Bid = 100. The Dealer Pays $150 and player keeps their bid
                Players that tied the dealer don't win, but don't lose anything

        {
            "_id": username,
            "ctx": interaction,
            "party_leader": bool,
            "hands": [hand(s)],
            "hand_total" = int,
            "card_information": {},
            "is_turn": Bool,
            "pile": {},
            'channel_id': channel_id
        }

        ex: Player who split their hand and doubled down on the right hand. Starting bid was $250
        {
            "_id": "Player1",
            "ctx": "<Class Object>",
            "party_leader": True,
            "hands": [
                {"hand": [{"card": "jack_of_spades", "value": 10}, {"card": "eight_of_hearts", "value": 8}], "bid" = 250, "hand_total" = 18},
                {"hand": [{"card": "jack_of_hearts", "value": 10}, {"card": "two_of_diamonds", "value": 2}], "bid" = 500, "hand_total" = 12}
            ],
            "is_turn": False,
            "pile": {dictionary containing all the cards},
            'channel_id': None
        }
        '''
    await interaction.response.send_message('WIP')

@tree.command(name="gofish", description="Play a game of Go-Fish with your friends! (CURRENTLY A WIP)")
async def _goFish(interaction, type: str):
    await interaction.response.send_message('WIP')

@tree.command(name="solitaire", description="Play a game of solitaire (CURRENTLY A WIP)")
async def _solitaire(interaction):
    await interaction.response.send_message('WIP')

@app_commands.describe(type = 'The argument to choose.')
@app_commands.choices(type = [
    app_commands.Choice(name = 'Open a Pack',                   value = 'open'),
    app_commands.Choice(name = 'View Your Deck',                value = 'deck'),
    app_commands.Choice(name = 'Create A Game',                 value = 'create'),
    app_commands.Choice(name = 'Start The Game',                value = 'start'),
    app_commands.Choice(name = '# Of Cards To Collect In Set.', value = 'collect'),
    app_commands.Choice(name = '# Of Cards Collected In Set',   value = 'collected')
])
@tree.command(name="card-jitsu", description="Please Type '/info card-jitsu' for information on this game!")
async def _cardJitsu(interaction, type: app_commands.Choice[str]):

    def update_view(username, hand):
        style = discord.ButtonStyle.gray
        view = discord.ui.View(timeout=None)
        
        buttons = []
        for card in range(len(hand)): buttons.append(discord.ui.Button(style=style, label=f'{card+1}', emoji=f'{hand[card]["card_image"]}'))

        for button in buttons:
            button.callback = get_function_callback(interaction_objects[username]['interaction'], int(button.label))
            view.add_item(button)

        interaction_objects[username]['view'] = view

    async def _update_window(username, turns_taken=0):

        players, _, _ = databasequery.player_lookup(username) # GOLLEM // GOLLEM
        for num in range(len(players)):

            # Updates image for everyone with new data

            hand = players[num]['hand']
            if players[num]['party_leader']:
                background = Image.open('./images/blue_control.png')
                for id in range(len(hand)):
                    card = Image.open(cardjitsuHandler.clubpenguincards[hand[id]['_id']])
                    card.thumbnail((100, 100), Image.ANTIALIAS)
                    background.paste(card, (75 + id*100, 585), card)
            else:
                background = Image.open('./images/yellow_control.png')
                for id in range(len(hand)):
                    card = Image.open(cardjitsuHandler.clubpenguincards[hand[id]['_id']])
                    card.thumbnail((100, 100), Image.ANTIALIAS)
                    background.paste(card, (575 + id*100, 585), card)
            
            # Places card on their penguin to show they took their turn
            if turns_taken != 0:
                for tt in range(len(players)):
                    if players[tt]['turn_taken']:
                        if turns_taken == 2: card_played = Image.open(cardjitsuHandler.clubpenguincards[players[tt]['card_information']['_id']])
                        else: card_played = Image.open('./images/colorElements/Card-Jitsu_card_back.png')
                        card_played.thumbnail((170, 170), Image.ANTIALIAS)
                        background.paste(card_played, (330 + 330*tt, 215), card_played)

            # Updates winning cards???
            hand_holder = [
                [players[0]['fire'], players[0]['water'], players[0]['snow']],
                [players[1]['fire'], players[1]['water'], players[1]['snow']]
            ]

            for hands in range(len(hand_holder)):
                for element in range(len(hand_holder[hands])):
                    for color in range(len(hand_holder[hands][element])):
                        dir = cardjitsuHandler.images[element][hand_holder[hands][element][len(hand_holder[hands][element]) - color - 1]]
                        symbol = Image.open(dir)
                        symbol.thumbnail((70, 70), Image.ANTIALIAS)
                        background.paste(symbol, (65 + element*75 + 765*hands, 70 + (len(hand_holder[hands][element]) - color - 1)*25), symbol)

            # Names
            draw = ImageDraw.Draw(background)
            font = ImageFont.truetype("./fonts/FreeSansBold.ttf", 30, encoding='unic')
            draw.text((70, 555), players[0]['_id'].upper(), (0, 0, 0), font=font)
            draw.text((1050 - 20*(len(players[1]['_id']) - 1), 555), players[1]['_id'].upper(), (0, 0, 0), font=font)

            # Shhh
            background.save('./images/VERSUS_CP.png')
            secret_channel = client.get_channel(1030955442769240116)
            file = discord.File("./images/VERSUS_CP.png", filename="VERSUS_CP.png")
            temp_message = await secret_channel.send(file=file)
            attachment = temp_message.attachments[0]

            # Editing the Embed
            embed = discord.Embed()
            embed.set_image(url=attachment.url)

            update_view(players[num]['_id'], hand)

            await interaction_objects[players[num]['_id']]['interaction'].edit_original_response(content='', embed=embed, view=interaction_objects[players[num]['_id']]['view'])

    # Add a waiting message for players when something goes through
    # Reenable if i somehow fix the infinite defer problem
    await interaction.response.defer()
    
    username = interaction.user.name
    send_message = True
    type = type.value

    # Opens a pack of cards and returns what they opened
    if type == 'open': 
        
        async def open_pack(interaction, set_number):
            cardsUnpacked = cardjitsuHandler.openPack(interaction.user.name, int(set_number))
            view = discord.ui.View()
            await interaction.edit_original_response(content=cardsUnpacked, view=view)
        
        style = discord.ButtonStyle.blurple

        buttons = []
        for i in range(8):
            buttons.append(discord.ui.Button(style=style, label=f'{i+1}'))
        
        def get_lambda(interaction, label):
            return lambda _: open_pack(interaction, label)

        view = discord.ui.View(timeout=None)
        for button in buttons:
            button.callback = get_lambda(interaction, button.label)
            view.add_item(button)

        await interaction.followup.send("Select A Series To Open", view=view)

    # Shows the user their collection of cards
    elif type == 'deck':
        cardsUnpacked = cardjitsuHandler.getDeck(username)
        allCards = ''

        # Checks if they even have a deck
        if cardsUnpacked == "Nothing Found!":
            await interaction.followup.send('Nothing Found!')
            return

        # Formats the print nicely
        for i in range(len(cardsUnpacked)):
            if len(allCards) + len(cardsUnpacked[i]['card_image']) >= 2000:
                await interaction.followup.send(allCards)
                allCards = ''
            allCards += cardsUnpacked[i]['card_image']
        
        await interaction.followup.send(allCards)
    
    # Creates a joinable server
    elif type == 'create':
        channel_id = interaction.channel_id
        started = cardjitsuHandler.createGame(interaction, username, channel_id)
        if "Your Game Code" in started: interaction_objects[interaction.user.name] = {'interaction': interaction}
        await interaction.followup.send(started)

    elif type == 'start':

        async def choose_card(interaction, number):
            
            username = interaction.user.name
            
            # Might be able to choose multiple cards at once? // FIX
            _, player, gameCollection = databasequery.player_lookup(username)

            # channel = client.get_channel(player['channel_id'])

            if player['turn_taken']: return

            players = cardjitsuHandler.takeTurn(username, number)
            
            # Gets current data for player
            for player in players:
                if player['_id'] == username:
                    break

            turns_taken = 0
            for player in players:
                if player['turn_taken']:
                    turns_taken += 1

            # Updates pile once both players have taken their turn
            if turns_taken == 2:

                await _update_window(username, 2)

                # Find the round winner and loser
                winner, loser = cardjitsuHandler.winningCard(username)

                # Finds if someone won the game as a whole
                winner_found = cardjitsuHandler.overall_winner(username)

                await _update_window(username)

                for player in players:
                    # channel = client.get_channel(player['channel_id'])

                    # Overall winner found, game ends
                    if winner_found:
                        cardjitsuHandler.pay_players(winner, loser)
                        _ = databasequery.abandonMatch(player['_id'], force=True)
                        view = discord.ui.View()
                        await interaction_objects[player['_id']]['interaction'].edit_original_response(content=f'{winner} won!', view=view)

            else: await _update_window(username, 1)

        def get_function_callback(interaction, number): return lambda _: choose_card(interaction, number)

        players, player, gameCollection = databasequery.player_lookup(username)
        
        if player == None:
            await interaction.followup.send('You\'re not in a game!')
            return

        send_message = True

        if not player['party_leader']:
            await interaction.followup.send("You're not the party leader!")
            return

        if len(players) < 2:
            await interaction.followup.send("There are not enough players to play!")
            return

        # Enough players and It's the Party Leader    
        for player in players:
            cardjitsuHandler.dealHands(player, gameCollection)

        players, player, gameCollection = databasequery.player_lookup(username)
        for player in players:
            # channel = client.get_channel(player['channel_id'])
            hand = player['hand']
            
            # Creating the Visuals
            if player['party_leader']:
                background = Image.open('./images/blue_control.png')
                for id in range(len(hand)):
                    card = Image.open(cardjitsuHandler.clubpenguincards[hand[id]['_id']])
                    card.thumbnail((100, 100), Image.ANTIALIAS)
                    background.paste(card, (75 + id*100, 580), card)
            else:
                background = Image.open('./images/yellow_control.png')
                for id in range(len(hand)):
                    card = Image.open(cardjitsuHandler.clubpenguincards[hand[id]['_id']])
                    card.thumbnail((100, 100), Image.ANTIALIAS)
                    background.paste(card, (575 + id*100, 580), card)

            draw = ImageDraw.Draw(background)
            font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 30, encoding='unic')
            draw.text((70, 555), players[0]['_id'].upper(), (0, 0, 0), font=font)
            draw.text((1050 - 20*(len(players[1]['_id']) - 1), 555), players[1]['_id'].upper(), (0, 0, 0), font=font)
            background.save('./images/VERSUS_CP.png')

            secret_channel = client.get_channel(1030955442769240116)
            file = discord.File("./images/VERSUS_CP.png", filename="VERSUS_CP.png")
            temp_message = await secret_channel.send(file=file)
            attachment = temp_message.attachments[0]

            embed = discord.Embed()
            embed.set_image(url=attachment.url)

            style = discord.ButtonStyle.gray
            view = discord.ui.View(timeout=None)
            
            buttons = []
            for card in range(len(hand)): buttons.append(discord.ui.Button(style=style, label=f'{card+1}', emoji=f'{hand[card]["card_image"]}'))

            for button in buttons:
                button.callback = get_function_callback(interaction_objects[player['_id']]['interaction'], int(button.label))
                view.add_item(button)

            interaction_objects[player['_id']]['view'] = view
            await interaction_objects[player['_id']]['interaction'].edit_original_response(embed=embed, view=view)
            # await temp_message.delete()

            await interaction_objects[player['_id']]['interaction'].followup.send('Please pick a card!')

    elif type == 'collect':

        async def to_collect(interaction, set_number):
            cardsToCollect = databasequery.collect(interaction.user.name, set_number, 'collect')
            view = discord.ui.View()
            await interaction.edit_original_response(content=cardsToCollect, view=view)

        style = discord.ButtonStyle.blurple

        buttons = []
        for i in range(8):
            buttons.append(discord.ui.Button(style=style, label=f'{i+1}'))
        
        def get_lambda(interaction, label):
            return lambda _: to_collect(interaction, label)

        view = discord.ui.View(timeout=None)
        for button in buttons:
            button.callback = get_lambda(interaction, button.label)
            view.add_item(button)

        await interaction.followup.send('Please Select A Series', view=view)

    elif type == 'collected':
        
        async def cards_collected(interaction, set_number):
            cardsCollected = databasequery.collect(interaction.user.name, set_number, 'collected')
            view = discord.ui.View()
            await interaction.edit_original_response(content=cardsCollected, view=view)

        style = discord.ButtonStyle.blurple

        buttons = []
        for i in range(8):
            buttons.append(discord.ui.Button(style=style, label=f'{i+1}'))
        
        def get_lambda(interaction, label):
            return lambda _: cards_collected(interaction, label)

        view = discord.ui.View(timeout=None)
        for button in buttons:
            button.callback = get_lambda(interaction, button.label)
            view.add_item(button)

        await interaction.followup.send('Please Select A Series', view=view)

    else: await interaction.followup.send("Failed To Execute Command!")

    if send_message:
        message = await interaction.followup.send('Boo')
        await message.delete()

@app_commands.describe(type     = 'The argument to choose.',
                       card     = 'The corresponding position of card in your hand.',
                       color    = 'Can be red, blue, yellow, or green',
                       call_uno = 'Used if you are going to have one card after placement.'
)
@app_commands.choices(type = [
    app_commands.Choice(name = 'Create A Game',                                         value = 'create'),
    app_commands.Choice(name = 'Start The Game',                                        value = 'start'),
    app_commands.Choice(name = 'Choose A Card In Hand. (Requires The "Card" Option)',   value = 'choose'),
    app_commands.Choice(name = 'Draw A Card',                                           value = 'draw'),
    app_commands.Choice(name = 'Call Uno! (Used If Another Player Has Uno)',            value = 'call uno')
])
@tree.command(name='uno', description='Play uno with your friends using this command!')
async def _uno(interaction, type: Literal['create', 'start', 'choose', 'draw', 'call uno'], card: str = None, color: str = None, call_uno: Literal['Uno!'] = None):

    await interaction.response.defer()

    if call_uno != None: call_uno = True
    if color != None: color = str(color).lower()
    type = str(type).lower()
    channel_id = interaction.channel_id
    username = interaction.user.name
    
    send_message = False

    if type == "create":
        started = databasequery.startGame(interaction, username, channel_id, "UNO", 8)
        await interaction.followup.send(started)
    
    elif type == 'start':

        _, inGame, _ = databasequery.player_lookup(username)
        
        if inGame != None:
            canStart = unoHandler.can_start(username)

            if canStart:
                message, pile = unoHandler.setup(username)

                if pile == None: await interaction.followup.send(message)
                else:

                    # Send all the players in their respective channels their hands.
                    players, _, gameCollection = databasequery.player_lookup(username)
                    channelCards = unoHandler.show_starting_hands(username)
                    count = 0

                    for user in channelCards:
                        userChannel = user[0]

                        channel = client.get_channel(userChannel)
                        embed = discord.Embed(title='^ YOUR HAND ^', color=0x00ff00)
                        handMessage = await channel.send(embed=embed, content=user[1])

                        # Gets messageID for editing. Clean Gameplay
                        hand_id = handMessage.id

                        embed = discord.Embed(title='^ PILE ^', color=0x00ff00)
                        pileMessage = await channel.send(embed=embed, content=pile['image'])

                        pile_id = pileMessage.id

                        gameCollection.update_one({'_id': players[count]['_id']}, {'$set': {'hand_id': hand_id}})
                        gameCollection.update_one({'_id': players[count]['_id']}, {'$set': {'pile_id': pile_id}})

                        if count != 0:
                            message = await channel.send(f'The Game has Begun! It\'s now {players[0]["_id"]}\'s turn!')
                            message_id = message.id
                            gameCollection.update_one({'_id': players[count]['_id']}, {'$set': {'message_id': message_id}})
                        
                        count += 1

                    channel = client.get_channel(channelCards[0][0])
                    message = await channel.send(content=f'It\'s your turn!')
                    message_id = message.id
                    gameCollection.update_one({'_id': username}, {'$set': {'message_id': message_id}})

                    await interaction.followup.send("Game Started!")

            else: await interaction.followup.send("The game has already begun!")
        else: await interaction.followup.send("You are not in a game!")

    elif type == 'choose':

        # player is in server
        _, inGame, _ = databasequery.player_lookup(username)

        if inGame != None:

            # Hand is empty so game hasn't started yet
            if inGame['hand'] != []:

                send_message = True

                # Is it the user's turn?
                isTurn, channel_id = unoHandler.is_turn(username)
                channel = client.get_channel(channel_id)
                if isTurn:

                    # Card can be placed on the pile?
                    if card == None: await interaction.followup.send('PLEASE SELECT A CARD')
                    else:
                        validCard, card, players = unoHandler.check_valid_card(username, int(card), color)
                        if validCard:

                            # Executes if a player hasn't won
                            hasWon = unoHandler.check_win(username)

                            if not hasWon:

                                # Player's card was valid and placed
                                colorChange = False
                                loop = 0
                                _, cards = unoHandler.showHand(username)
                                embed = discord.Embed(title='^ YOUR HAND ^', color=0x00ff00)
                    
                                hand = ''
                                for image in cards:
                                    hand += image['image'] + ''

                                _, player, _ = databasequery.player_lookup(interaction.user.name)
                                message = await channel.fetch_message(player['hand_id'])
                                await message.edit(embed=embed, content=hand)

                                # Add a state if and when new cards are added
                                if card['type'] == 'plustwo': loop = 2
                                elif card['type'] == 'plusfour':
                                    colorChange = True
                                    loop = 4
                                elif card['type'] == 'wild': colorChange = True
                                elif card['type'] == 'reverse': unoHandler.reverse(username)

                                # Turn is passed over
                                next_player_channel, next_player_name = unoHandler.pass_turn(username)
                                channel = client.get_channel(next_player_channel)

                                # Runs if the player needs to draw cards and skips them
                                cards_drawn = ''
                                count = 0
                                for i in range(loop):
                                    message, _ = unoHandler.draw_card(next_player_name)
                                    cards_drawn += message + ' '
                                    count += 1

                                    if i == loop-1:

                                        _, cards = unoHandler.showHand(next_player_name)

                                        embed = discord.Embed(title='^ YOUR HAND ^', color=0x00ff00)
                    
                                        hand = ''
                                        for image in cards:
                                            hand += image['image'] + ''

                                        _, player, _ = databasequery.player_lookup(next_player_name)
                                        message = await channel.fetch_message(player['hand_id'])
                                        await message.edit(embed=embed, content=hand)

                                        next_player_channel, next_player_name = unoHandler.pass_turn(next_player_name)
                                
                                # Runs if the player was skipped
                                if card['type'] == 'skip':
                                    next_player_channel, next_player_name = unoHandler.pass_turn(next_player_name)
                                
                                players, person, gameCollection = databasequery.player_lookup(username)

                                # Returns to all players the new pile
                                for player in players:
                                    embed = discord.Embed(title='^ PILE ^', color=0x00ff00)
                                    
                                    channel = client.get_channel(player['channel_id'])
                                    message = await channel.fetch_message(player['pile_id'])
                                    await message.edit(embed=embed, content=card['image'])

                                    if colorChange: added_color = f'\nThe pile color is now: {card["color"]}!'
                                    else: added_color = ''
                                    
                                    if colorChange and player['_id'] != username and player['_id'] != next_player_name:
                                        msg_id = databasequery.get_msg_id(player['_id'])
                                        msg = await channel.fetch_message(msg_id)
                                        await msg.edit(content=f'The pile color is now: {card["color"]}!')

                                # Checks if an uno happened and sends everybody
                                # Except that player that they got an uno if not called correctly
                                isUno = unoHandler.check_uno(username)
                                if isUno and not call_uno: uno_message = f'\nPsst! Looks like {username} forgot to call uno. Try to call uno before they notice!'
                                else:
                                    # Uno was called but they have more than 1 card in their hand
                                    if call_uno and not isUno:
                                        hand = ''

                                        for card in person['hand']:
                                            hand += card['image']

                                        for _ in range(2):
                                            card, _ = unoHandler.draw_card(username)
                                            hand += card # already an image

                                        embed = discord.Embed(title='^ YOUR HAND ^', color=0x00ff00)
                                        message = await channel.fetch_message(person['hand_id'])
                                        await message.edit(embed=embed, content=hand)

                                    uno_message = ''

                                msg_id = databasequery.get_msg_id(next_player_name)
                                channel = client.get_channel(next_player_channel)
                                msg = await channel.fetch_message(msg_id)
                                await msg.edit(content=f'{next_player_name}, It\'s your turn!{added_color}{uno_message}')

                                for player in players:
                                    msg_id = databasequery.get_msg_id(player['_id'])
                                    channel = client.get_channel(player['channel_id'])
                                    msg = await channel.fetch_message(msg_id)

                                    message = f'It is now {next_player_name}\'s turn!{added_color}'


                                    if player['_id'] != username and player['channel_id'] != next_player_channel:
                                        await msg.edit(content=message + uno_message)

                                    elif player['_id'] == username:
                                        await msg.edit(content=message)
                            else:
                                # Player won the game, game is over.
                                players, player, _ = databasequery.player_lookup(username)

                                for person in players:
                                    
                                    channel = client.get_channel(person['channel_id'])

                                    embed = discord.Embed(title='^ PILE ^', color=0x00ff00)
                                    message = await channel.fetch_message(person['pile_id'])
                                    await message.edit(embed=embed, content=card['image'])

                                    if person['channel_id'] != player['channel_id']:
                                        msg_id = databasequery.get_msg_id(person['_id'])
                                        msg = await channel.fetch_message(msg_id)
                                        await msg.edit(content=f'GAME OVER: {username} wins!')
                                
                                msg_id = databasequery.get_msg_id(username)
                                channel = client.get_channel(player['channel_id'])
                                msg = await channel.fetch_message(msg_id)
                                await msg.edit(content='GAME OVER: You win!')

                                embed = discord.Embed(title='^ HAND ^', color=0x00ff00)
                                message = await channel.fetch_message(player['hand_id'])
                                await message.edit(embed=embed, content=player['hand'])

                                databasequery.abandonMatch(username, force=True)

                        else:
                            msg_id = databasequery.get_msg_id(username)
                            msg = await channel.fetch_message(msg_id)
                            await msg.edit(content='That card and/or color is invalid!')
                else:
                    msg_id = databasequery.get_msg_id(username)
                    channel = client.get_channel(channel_id)
                    msg = await channel.fetch_message(msg_id)
                    await msg.edit(content="It's not your turn!")
            else:
                await interaction.followup.send("The game hasn't started yet!")
        else:
            await interaction.followup.send('You\'re not in a game!')

    elif type == 'draw':

        # Can only draw when its your turn | FIX
        players, player, _ = databasequery.player_lookup(username)

        if player != None:
            send_message = True

            if player['hand'] != []:
                if player['is_turn']:
                    message, user_channel = unoHandler.draw_card(username)

                    if user_channel != None:

                        channel, cards = unoHandler.showHand(username)

                        embed = discord.Embed(title='^ YOUR HAND ^', color=0x00ff00)
                        
                        hand = ''
                        for card in cards:
                            hand += card['image'] + ''

                        channel = client.get_channel(channel)
                        msg_id = await channel.fetch_message(player['hand_id'])
                        await msg_id.edit(embed=embed, content=hand)

                        next_player_channel, next_player_name = unoHandler.pass_turn(username)
                        channel = client.get_channel(next_player_channel)

                        next_player_msg_id = databasequery.get_msg_id(next_player_name)
                        msg = await channel.fetch_message(next_player_msg_id)
                        await msg.edit(content=f'{username} drew a card. It\'s now your turn, {next_player_name}!')

                        msg_id = databasequery.get_msg_id(username)
                        channel = client.get_channel(user_channel)
                        msg = await channel.fetch_message(msg_id)
                        await msg.edit(content=f"You drew a card! It's now {next_player_name}'s turn!")

                        for player in players:
                            if player['_id'] != username and player['_id'] != next_player_name:
                                msg_id = databasequery.get_msg_id(player['_id'])
                                channel = client.get_channel(player['channel_id'])
                                msg = await channel.fetch_message(msg_id)
                                await msg.edit(content=f'{username} drew a card. It\'s now {next_player_name}\'s turn!')
                    else:
                        msg_id = databasequery.get_msg_id(username)
                        msg = await user_channel.fetch_message(msg_id)
                        await msg.edit(content=message)
                else:
                    msg_id = databasequery.get_msg_id(username)
                    channel = client.get_channel(player['channel_id'])
                    msg = await channel.fetch_message(player['message_id'])
                    await msg.edit(content='It\'s not your turn yet!')
            else:
                await interaction.followup.send('The game has not yet begun!')
        else:
            await interaction.followup.send('You are not in a game!')

    elif type == 'call uno':

        _, inGame, _ = databasequery.player_lookup(username)
        
        if inGame != None:

            # Players hand is empty, so game hasn't started
            if inGame['hand'] != []:

                send_message = True

                cards, unoUsersChannel = unoHandler.callout(username)

                if unoUsersChannel != None:
                    
                    players, _, _ = databasequery.player_lookup(username)

                    users_turn = ''

                    for player in players:
                        if player['channel_id'] == unoUsersChannel:
                            playerHasUno = player['_id']
                            player_to_draw = player

                        if player['is_turn']:
                            users_turn = player['_id']

                    for person in players:
                        if person['channel_id'] != player['channel_id']:
                            channel = client.get_channel(person['channel_id'])
                            message = await channel.fetch_message(person['message_id'])
                            
                            await message.edit(content = f'{username} called uno, {playerHasUno} draws 2 cards!\nIt is still {users_turn}\'s turn!')

                    embed = discord.Embed(title='^ YOUR HAND ^', color=0x00ff00)
                    channel = client.get_channel(player_to_draw['channel_id'])
                    hand = ''
                    for card in player_to_draw['hand']:
                        hand += card['image'] + ''

                    message = await channel.fetch_message(player_to_draw['hand_id'])
                    await message.edit(embed=embed, content=hand)
                else:
                    _, player, _ = databasequery.player_lookup(username)
                    channel = client.get_channel(player['channel_id'])
                    message = await channel.fetch_message(player['message_id'])
                    await message.edit(content=cards)
            else:
                await interaction.followup.send('The game hasn\'t started yet!')
        else:
            await interaction.followup.send('You\'re not in a game!')
    
    else: await interaction.followup.send("Please give a valid response!")

    if send_message:
        message = await interaction.followup.send('Boo')
        await message.delete()

@app_commands.describe(key='The game\'s key, aquired from /games')
@tree.command(name="join", description='Join servers using this command!')
async def _join(interaction, key: str):
    await interaction.response.defer()

    channel_id = interaction.channel_id
    username = interaction.user.name

    valid_server = databasequery.valid_server(key)

    if valid_server:

        # Checks to see if the game has already begun
        game_started = databasequery.game_started(key)

        if not game_started:
            joined = databasequery.joinGame(interaction, username, key, channel_id)

            if joined == 'Successfully Connected To Server!':
                players, _, _ = databasequery.player_lookup(username)

                for player in players:
                    if player['_id'] != username:
                        channel = client.get_channel(player['channel_id'])
                        await channel.send(f'{username} has joined the game!')

            await interaction.followup.send(joined)
        else:
            await interaction.followup.send("This game has already started!")
    else:
        await interaction.followup.send('That server doesn\'t exist! Please check the key and try again!')

@tree.command(name="games", description='View servers to join using this command!')
async def _games(interaction):
    games = databasequery.showGames()

    allContent = ''
    for game in range(len(games)):
        key = list(games[game].keys())
        values = list(games[game].values())[0]
        allContent += key[0] + ': '

        for value in range(len(values)):
            if value == len(values) - 1: allContent += values[value]
            else: allContent += values[value] + ', '

        allContent += '\n'

    embed = discord.Embed(title='ACTIVE GAMES', description = allContent, color=0x00ff00)

    await interaction.response.send_message(embed=embed)

@tree.command(name="abandon", description='Abandons the game you\'re in.')
async def _abandon(interaction):

    username = interaction.user.name

    players, player, _ = databasequery.player_lookup(username)

    if player != None:

        for person in players:
            if person['channel_id'] != player['channel_id']:
                channel = client.get_channel(person['channel_id'])
                await channel.send(f'{username} has left the game!')

        if player['party_leader']:
            for person in players:
                if person['channel_id'] != player['channel_id']:
                    channel = client.get_channel(person['channel_id'])
                    await channel.send('The game has been disbanded by the party leader!')

        abandonMessage = databasequery.abandonMatch(username)
        await interaction.response.send_message(abandonMessage)

    else:
        await interaction.response.send_message('You\'re not in a game to abandon!')

@tree.command(name='lobby', description='A way of checking all of the players in your lobby!')
async def _lobby(interaction):
    username = interaction.user.name

    players, _, gameCollection = databasequery.player_lookup(username)

    list_of_players = ''

    if players != None:
        for player in range(len(players)):
            if player != len(players) - 1: list_of_players += players[player]['_id'] + '\n'
            else: list_of_players += players[player]['_id']

        embed = discord.Embed(title=f'Lobby: {gameCollection.name}', description=list_of_players, color=0x00ff00)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("You're not in a game!")

@app_commands.describe(message='The Message You Are Sending')
@tree.command(name="report", description="This is a function to report bugs for the bot!")
async def _report(interaction, message: str):
    databasequery.send_report(message, interaction.user.name)
    await interaction.response.send_message('Report Submitted!')

@app_commands.describe(message='The Message You Are Sending')
@tree.command(name="suggestion", description="This is a function to suggest features or implementations for the bot!")
async def _suggestion(interaction, message: str):
    databasequery.send_suggestion(message, interaction.user.name)
    await interaction.response.send_message('Suggestion Received!')

@tree.command(name='rules', description='A Command To See How To Play These Games!')
async def _rules(interaction):
    embed=discord.Embed(
        title="Rules",
        description="Here you can learn how to play these games!\n\n" + \
        '**PARTY GAMES**\n'
        '[Uno](https://www.ultraboardgames.com/uno/game-rules.php)\n' + \
        '[GoFish](https://bicyclecards.com/how-to-play/go-fish/)\n' + \
        '[Card-Jitsu](https://clubpenguin.fandom.com/wiki/Card-Jitsu)\n' + \
        '[Chess](https://www.chess.com/learn-how-to-play-chess)\n' + \
        '[Exploding Kittens](https://www.explodingkittens.com/pages/rules-kittens)\n' + \
        '[Apples To Apples](https://service.mattel.com/instruction_sheets/N1488-0920.pdf)\n\n' + \
        '**CASINO GAMES**\n' + \
        '[BlackJack](https://wizardofodds.com/games/blackjack/basics/#rules) \n' + \
        '[Texas Holdem](https://wizardofodds.com/games/texas-hold-em/)\n' + \
        '[Baccarat](https://wizardofodds.com/games/three-card-baccarat/)\n' + \
        '[Oasis Poker](https://wizardofodds.com/games/oasis-poker/)\n' + \
        '[Three Card Poker](https://www.caesars.com/casino-gaming-blog/latest-posts/poker/how-to-play-three-card-poker#.Y0mhUkrMKV4)\n\n' + \
        '**Single-Player Games**\n'
        '[Solitaire](https://bicyclecards.com/how-to-play/solitaire/)\n' + \
        '[Minesweeper](https://www.instructables.com/How-to-play-minesweeper/)',
        color=0xFF5733)

    await interaction.response.send_message(embed=embed)

@tree.command(name="test", description="This is a test function for DM's!")
async def _test(interaction):
    with open('images/yellow_control.png', 'rb') as f:
        file = discord.File(f)
    await interaction.response.send_message(file=file)

@client.event
async def on_ready():
    await tree.sync()
    print("ONLINE")

# async def check_user():
#     # Autonomous running function
#     pass

# client.loop.create_task(check_user())
client.run(TOKEN)

'''
Games to Develop
    Apples to Apples
    Cards Against Humanity
    Texas Holdem
    GoFish
    Chess
    Golf
    Yahtzee
    Exploding
    BlackJack
    Baccarat
    Oasis Poker
    Three Card Poker
    Solitaire
    Minesweeper
'''