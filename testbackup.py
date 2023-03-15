from dotenv.main import load_dotenv
import discord
from discord import app_commands
import os
from datetime import datetime
import random
from PIL import Image, ImageDraw, ImageFont
from cardgames.database import DatabaseQuery
from cardgames.cardjitsu import CardJitsu
from cardgames.uno.uno import Uno
from typing import Literal
from cardgames.uno.drawunoscene import DrawUnoScene

load_dotenv()
TOKEN = os.getenv('TOKEN')
database = os.getenv('MONGO_TOKEN')

databasequery = DatabaseQuery(database)
cardjitsuHandler = CardJitsu(database, databasequery)
unoHandler = Uno(databasequery)

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

bot_start_time = datetime.now()
guilds = [discord.Object(id=989412607335227402), discord.Object(id=1030955442198822933)]

# Stores everyone's interaction for sending/editing messages
    # i.e. {'mathidiot', <discord.Interaction> object}
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

    else:
        await interaction.followup.send("Failed To Execute Command!")

    if send_message:
        message = await interaction.followup.send('Boo')
        await message.delete()

@tree.command(name='uno', description='Play uno with your friends using this command!')
async def _uno(interaction, type: Literal['create', 'start']):

    # TODO
    # Color buttons Green and Red based on possible choices to place down // Experimental
    # Unlimited Hand Size

    def return_draw_lambda(interaction, access): return lambda _: draw_card(interaction, access)
    def get_function_callback(interaction, card, access): return lambda _: choose_card(interaction, card, access)
    def recover_hands(players): return lambda _: update_hand(interaction = None, cards=None, players=players)
    def return_callout_function(username): return lambda _: call_uno(username)
    def return_page(username, access): return lambda _: update_hand(None, None, players=[{'_id': username}], access=access)
    
    async def color_callback(username, response, view, card, color):
        users, _, gameCollection = databasequery.player_lookup(username)

        view.on_timeout = None
        for user in users:
            await interaction_objects[user['_id']]['interaction'].followup.send(response, ephemeral=True)
        
        card['color'] = color
        leader = unoHandler.find_leader(users)
        gameCollection.update_one({'_id': leader['_id']}, {"$set": {'pile': card}})

    async def timeout_message(username, card):
        users, _, gameCollection = databasequery.player_lookup(username)
        
        color = random.choice(['red', 'yellow', 'blue', 'green'])
        for user in users:
            await interaction_objects[user['_id']]['interaction'].followup.send(f'The pile color is {color}', ephemeral=True)

        card['color'] = color
        leader = unoHandler.find_leader(users)
        gameCollection.update_one({'_id': leader['_id']}, {"$set": {'pile': card}})

    async def update_visuals(username, game_over=False):
        players, _, _ = databasequery.player_lookup(username)
        for i in players:
            try:
                pile = i['pile']
                break
            except: pass
        
        # A reverse was played
        if not players[0]['party_leader']: players.reverse()

        names = [player['_id'].upper() for player in players]
        hands = [player['hand'] for player in players]
        drawscene = DrawUnoScene(players, names, hands, pile)
        drawscene.update_window()

        # Shhh
        secret_channel = client.get_channel(1030955442769240116)
        file = discord.File("./images/TableWithUno.png", filename="TableWithUno.png")
        temp_message = await secret_channel.send(file=file)
        attachment = temp_message.attachments[0]

        # Editing the Embed
        embed = discord.Embed()
        embed.set_image(url=attachment.url)

        if game_over:
            view = discord.ui.View()
            await interaction_objects[players[0]['_id']]['interaction'].edit_original_response(embed=embed, view = view)
        else: await interaction_objects[players[0]['_id']]['interaction'].edit_original_response(embed=embed)

    async def call_uno(username):

        players, _, _ = databasequery.player_lookup(username)

        callout = unoHandler.callout(username)

        # Person was called out for having uno
        if callout[0] == 'caught':

            # Update hand of the person who was caught
            _, cards = unoHandler.showHand(callout[2])
            await update_hand(interaction_objects[callout[2]]['interaction'], cards)

            # Tells everyone the person was caught before calling themselves for uno
            for player in players:
                await interaction_objects[player['_id']]['interaction'].followup.send(content = f'{username} called uno, {callout[2]} draws 2 cards!', ephemeral=True)
            
            # Update the visuals to show the player drew 2 cards
            await update_visuals(username)

        # Player called themselves for uno so they are safe
        elif callout == 'safe':
            for player in players:
                await interaction_objects[player['_id']]['interaction'].followup.send(content = f'{username} called uno on themselves. They are safe!', ephemeral=True)

        else:
            await interaction_objects[username]['interaction'].followup.send(content = 'There are no users with uno to callout!', ephemeral=True)

    async def draw_card(interaction, access=0):
        username = interaction.user.name
        _, player, _ = databasequery.player_lookup(username)
            
        if not player['is_turn']:
            await interaction.followup.send('It\'s not your turn yet!', ephemeral=True)
            return

        message, user_channel = unoHandler.draw_card(username)

        if user_channel == None:
            msg_id = databasequery.get_msg_id(username)
            msg = await user_channel.fetch_message(msg_id)
            await msg.edit(content=message)
            return

        _, cards = unoHandler.showHand(username)

        await update_hand(interaction_objects[username]['interaction'], cards, access=access)

        unoHandler.pass_turn(username)
        await update_visuals(username)

    async def update_hand(interaction, cards, players=None, access=0):

        # Updates just the one player's hand
        if interaction != None: players = ['base']
        
        for player in players:
            if player != 'base':
                _, player, _ = databasequery.player_lookup(player['_id'])
                if len(players) != 1: interaction_objects[player['_id']]['ephemeral'] = None
                interaction = interaction_objects[player['_id']]['interaction']
                cards = player['hand']

            username = interaction.user.name
            # views = [discord.ui.View(timeout=None) for _ in range((len(cards)/21).__ceil__())]
            views = [discord.ui.View(timeout=None) for _ in range((len(cards)/8).__ceil__())]

            # Call Uno Button
            callUnoButton = discord.ui.Button(style=discord.ButtonStyle.blurple, label='Call Uno!')
            callUnoButton.callback = return_callout_function(username)
            
            for view in range(len(views)):
                # Draw Card Button
                drawButton = discord.ui.Button(style=discord.ButtonStyle.blurple, label='Draw')
                drawButton.callback = return_draw_lambda(interaction, view)    
                
                views[view].add_item(drawButton)
                views[view].add_item(callUnoButton)

            buttons = []
            for item in range(len(cards)):
                buttons.append(discord.ui.Button(style=style, label=f'{cards[item]["color"]} {cards[item]["type"]}', emoji=f'{cards[item]["image"]}'))

            # Add all buttons to view
            view = 0
            for button in range(len(buttons)):
                buttons[button].callback = get_function_callback(interaction, button+1, view)
                views[view].add_item(buttons[button])
                # if (button + 1) % 21 == 0: view += 1
                if (button + 1) % 8 == 0: view += 1

            # Create Prev/Next buttons for respective views
            for view in range(len(views)):
                if len(views) == 1: break

                next_page = discord.ui.Button(style=discord.ButtonStyle.blurple, label='Next Page')
                prev_page = discord.ui.Button(style=discord.ButtonStyle.blurple, label='Prev Page')

                next_page.callback = return_page(username, view+1)
                prev_page.callback = return_page(username, view-1)
                
                # First view in array
                if view == 0: views[view].add_item(next_page)
                # Last view in array
                elif view == len(views) - 1: views[view].add_item(prev_page)
                # Any other view in array
                else:
                    views[view].add_item(prev_page)
                    views[view].add_item(next_page)

            interaction_objects[username]['view'] = views
            
            # Updating the user's hand
            try:
                await interaction_objects[username]['ephemeral'].edit(view=views[access])
            except:
                # User emptied one page of cards
                try:
                    await interaction_objects[username]['ephemeral'].edit(view=views[0])
                # User recovered their hand
                except:
                    ephemeral = await interaction.followup.send(view=views[access], ephemeral=True)
                    interaction_objects[username]['ephemeral'] = ephemeral

    async def choose_card(interaction, card, access=0):
        # player is in server
        username = interaction.user.name

        # Is it the user's turn?
        isTurn, channel_id = unoHandler.is_turn(username)
        
        if not isTurn:
            await interaction.followup.send("It's not your turn!", ephemeral=True)
            return

        validCard, card, players = unoHandler.check_valid_card(username, int(card))
        if not validCard:
            await interaction.followup.send('That\'s not a valid card!', ephemeral=True)
            return

        if card['color'] == 'any':
            # Have user change the color of the table if a wild was played

            style = discord.ButtonStyle.gray
            view = discord.ui.View(timeout=15)
            view.on_timeout = lambda: timeout_message(username, card)
            
            red = discord.ui.Button(style=style, label='red')
            blue = discord.ui.Button(style=style, label='blue')
            yellow = discord.ui.Button(style=style, label='yellow')
            green = discord.ui.Button(style=style, label='green')

            red.callback =    lambda _: color_callback(username, 'The pile color is red!',    view, card, red.label)
            blue.callback =   lambda _: color_callback(username, 'The pile color is blue!',   view, card, blue.label)
            yellow.callback = lambda _: color_callback(username, 'The pile color is yellow!', view, card, yellow.label)
            green.callback =  lambda _: color_callback(username, 'The pile color is green!',  view, card, green.label)

            view.add_item(red)
            view.add_item(blue)
            view.add_item(yellow)
            view.add_item(green)

            await interaction.followup.send(f"Pick a color! (you have 15 seconds)", view=view, ephemeral=True)

        # Executes if a player hasn't won
        hasWon = unoHandler.check_win(username)

        if not hasWon:

            # Player's card was valid and placed
            colorChange = False
            loop = 0
            _, cards = unoHandler.showHand(username)
            await update_hand(interaction_objects[username]['interaction'], cards, access=access)

            # Add a state if and when new cards are added
            if card['type'] == 'plustwo': loop = 2
            elif card['type'] == 'plusfour': loop = 4
            elif card['type'] == 'reverse': unoHandler.reverse(username)

            _, next_player_name = unoHandler.pass_turn(username)

            # Runs if the player needs to draw cards and skips them
            for i in range(loop):
                _, _ = unoHandler.draw_card(next_player_name)

                if i == loop-1:
                    _, cards = unoHandler.showHand(next_player_name)
                    await update_hand(interaction_objects[next_player_name]['interaction'], cards)
                    _, next_player_name = unoHandler.pass_turn(next_player_name)
            
            # Runs if the player was skipped
            if card['type'] == 'skip': _, next_player_name = unoHandler.pass_turn(next_player_name)
            await update_visuals(username)
        else:

            # Player won the game, game is over.
            players, _, _ = databasequery.player_lookup(username)

            await update_visuals(username, game_over = True)

            for person in players:
                await interaction_objects[person['_id']]['interaction'].followup.send(f'GAME OVER: {username} wins!', ephemeral=True)
            
            for player in players:
                if player['party_leader']: databasequery.abandonMatch(player['_id'], force=True)
                interaction_objects.__delitem__(player['_id'])

    await interaction.response.defer()

    # if call_uno != None: call_uno = True
    type = str(type).lower()
    channel_id = interaction.channel_id
    username = interaction.user.name
    
    send_message = False

    if type == "create":
        started = databasequery.startGame(interaction, username, channel_id, "UNO", 8)
        if "Your Game Code" in started: interaction_objects[interaction.user.name] = {'interaction': interaction}
        await interaction.followup.send(started)
    
    elif type == 'start':

        interaction_objects[interaction.user.name]['interaction'] = interaction

        _, inGame, _ = databasequery.player_lookup(username)
        
        if inGame == None:
            await interaction.followup.send("You are not in a game!")
            return
        
        canStart = unoHandler.can_start(username)

        if not canStart:
            await interaction.followup.send("The game has already begun!")
            return

        message, pile = unoHandler.setup(username)

        if pile == None:
            await interaction.followup.send(message)
            return

        # Send all the players in their respective channels their hands.
        players, player, _ = databasequery.player_lookup(username)

        names = [player['_id'].upper() for player in players]
        hands = [player['hand'] for player in players]
        drawscene = DrawUnoScene(players, names, hands, pile)
        drawscene.update_window()

        # Send the button to recover messages
        style = discord.ButtonStyle.gray
        view = discord.ui.View(timeout=None)
        recover_hands_button = discord.ui.Button(style=style, label='Recover Hand')
        recover_hands_button.callback = recover_hands(players)
        view.add_item(recover_hands_button) 

        # Shhh
        secret_channel = client.get_channel(1030955442769240116)
        file = discord.File("./images/TableWithUno.png", filename="TableWithUno.png")
        temp_message = await secret_channel.send(file=file)
        attachment = temp_message.attachments[0]

        # Editing the Embed
        embed = discord.Embed()
        embed.set_image(url=attachment.url)

        # Send the board
        await interaction_objects[player['_id']]['interaction'].followup.send(embed=embed, view=view)

        # Send players their hands as an ephemeral
        for player in players:
            await update_hand(interaction_objects[player['_id']]['interaction'], player['hand'])
    
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

    if not valid_server:
        await interaction.followup.send('That server doesn\'t exist! Please check the key and try again!')
        return

    # Checks to see if the game has already begun
    game_started = databasequery.game_started(key)

    if game_started:
        await interaction.followup.send("This game has already started!")
        return

    joined = databasequery.joinGame(interaction, username, key, channel_id)

    if joined == 'Successfully Connected To Server!':
        interaction_objects[username] = {'interaction': interaction}
        players, _, _ = databasequery.player_lookup(username)

        for player in players:
            if player['_id'] != username:
                # channel = client.get_channel(player['channel_id'])
                await interaction_objects[player['_id']]['interaction'].followup.send(f'{username} has joined the game!')

    await interaction.followup.send(joined)

@tree.command(name="abandon", description='Abandons the game you\'re in.')
async def _abandon(interaction):

    username = interaction.user.name

    players, player, _ = databasequery.player_lookup(username)

    if player == None:
        await interaction.response.send_message('You\'re not in a game to abandon!')
        return

    for person in players:
        if person['_id'] != username:
            await interaction_objects[person['_id']]['interaction'].followup.send(f'{username} has left the game!')

    if player['party_leader']:
        for person in players:
            if person['_id'] != username:
                await interaction_objects[person['_id']]['interaction'].followup.send('The game has been disbanded by the party leader!')

    abandonMessage = databasequery.abandonMatch(username)
    await interaction.response.send_message(abandonMessage)

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

    style = discord.ButtonStyle.gray
    
    cards = 48
    views = [discord.ui.View(timeout=None)]
    buttons = []
    for i in range(cards):
        if i % 24 == 0 and i != 0:
            button = discord.ui.Button(style=style, label='Next Page')
            buttons.append(button)
            button = discord.ui.Button(style=style, label=i+1)
        elif i % 23 == 0 and i != 23 and i != 0:  
            button = discord.ui.Button(style=style, label='Prev Page')
        else:
            button = discord.ui.Button(style=style, label=i+1)
        buttons.append(button)

    for button in buttons:
        views[-1].add_item(button)
        if button.label == 'Next Page': views.append(discord.ui.View(timeout=None))

    await interaction.response.send_message(f"Total Cards!", view=views[0], ephemeral=True)
    await interaction.followup.send(view=views[1], ephemeral=True)
    await interaction.followup.send(view=views[2], ephemeral=True)

@client.event
async def on_reaction_add(reaction, user):
    print(reaction, user)

@client.event
async def on_reaction_remove(reaction, user):
    print(reaction, user)

@client.event
async def on_ready():
    await tree.sync()
    print("ONLINE")

client.run(TOKEN)

# FUNCTIONS TO FIX
'''
balance - Visuals?
daily - Visuals?
weekly - Visuals?
monthly - Visuals?
games - Visuals?
lobby - Visuals?
'''

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