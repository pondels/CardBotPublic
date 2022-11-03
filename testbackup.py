from dotenv.main import load_dotenv
import discord
from discord import app_commands
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from cardgames.database import DatabaseQuery
from cardgames.cardjitsu import CardJitsu
from cardgames.uno import Uno
from typing import Literal
import time

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

@app_commands.describe(type       = 'The argument to choose.',
                       number     = 'The corresponding position of card in your hand. 1 - 5',
                       set_number = 'The set number to open packs. Sets (1 - 8)'
)
@app_commands.choices(type = [
    app_commands.Choice(name = 'Open a Pack. (Requires the Set_Number Option)',              value = 'open'),
    app_commands.Choice(name = 'View Your Deck',                                             value = 'deck'),
    app_commands.Choice(name = 'Create A Game',                                              value = 'create'),
    app_commands.Choice(name = 'Start The Game',                                             value = 'start'),
    app_commands.Choice(name = 'Select A Card',                                              value = 'choose'),
    app_commands.Choice(name = '# Of Cards To Collect In Set. (Requires Set_Number Option)', value = 'collect'),
    app_commands.Choice(name = '# Of Cards Collected In Set (Requires Set_Number Option)',   value = 'collected')
])
@tree.command(name="card-jitsu", description="Please Type '/info card-jitsu' for information on this game!")
async def _cardJitsu(interaction, type: app_commands.Choice[str], number: Literal['1', '2', '3', '4', '5'] = None, set_number: Literal['1', '2', '3', '4', '5', '6', '7', '8'] = None):

    async def _update_window(username, turns_taken=0):

        players, _, _ = databasequery.player_lookup(username) # GOLLEM // GOLLEM
        for num in range(len(players)):

            # Updates image for everyone with new data
            channel = client.get_channel(players[num]['channel_id'])
            hand_id = await channel.fetch_message(players[num]['hand_id'])

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
            await hand_id.edit(content='', embed=embed)
            await temp_message.delete()

    # Add a waiting message for players when something goes through
    # Reenable if i somehow fix the infinite defer problem
    await interaction.response.defer()
    
    username = interaction.user.name
    send_message = True
    type = type.value

    # Opens a pack of cards and returns what they opened
    if type == 'open':
        if set_number != None:
            cardsUnpacked = cardjitsuHandler.openPack(username, int(set_number))
        else: cardsUnpacked = "Please Select a Pack Number!"
        await interaction.followup.send(cardsUnpacked)

    # Shows the user their collection of cards
    elif type == 'deck':
        cardsUnpacked = cardjitsuHandler.getDeck(username)
        allCards = ''

        # Checks if they even have a deck
        if cardsUnpacked != "Nothing Found!":
            # Formats the print nicely
            for i in range(len(cardsUnpacked)):
                if len(allCards) + len(cardsUnpacked[i]['card_image']) >= 2000:
                    await interaction.followup.send(allCards)
                    allCards = ''
                allCards += cardsUnpacked[i]['card_image']
            if allCards != '': await interaction.followup.send(allCards)
        else: await interaction.followup.send('Nothing Found!')
    
    # Creates a joinable server
    elif type == 'create':
        channel_id = interaction.channel_id
        started = cardjitsuHandler.createGame(interaction, username, channel_id)
        if "Your Game Code" in started: interaction_objects[interaction.user.name] = interaction
        await interaction.followup.send(started)

    elif type == 'start':
        
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
        
        # Enough players and It's the Party Leader    
        for player in players:
            cardjitsuHandler.dealHands(player, gameCollection)

        players, player, gameCollection = databasequery.player_lookup(username)
        for player in players:
            channel = client.get_channel(player['channel_id'])
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
            message = await channel.send(embed=embed)
            hand_id = message.id
            await temp_message.delete()

            message = await channel.send(content='Please pick a card!')
            message_id = message.id

            gameCollection.update_one({'_id': player['_id']}, {'$set': {'hand_id': hand_id}})
            gameCollection.update_one({'_id': player['_id']}, {'$set': {'message_id': message_id}})

    elif type == 'choose':

        # Might be able to choose multiple cards at once? // FIX
        _, player, gameCollection = databasequery.player_lookup(username)

        if player == None:
            await interaction.followup.send('You are not in a game!')
            return

        # Players hand is empty, game hasn't started
        if player['hand'] == []:
            await interaction.followup.send('The game has not started yet!')
            return

        number = int(number)

        channel = client.get_channel(player['channel_id'])
        if number < 1 or number > 5:
            msg_channel = await channel.fetch_message(player['message_id'])
            await msg_channel.edit(content="Please choose a number 1 - 5")
            return

        if player['turn_taken']:
            msg_channel = await channel.fetch_message(player['message_id'])
            await msg_channel.edit(content="You have already taken your turn. Please wait for your opponent to choose a card!")
            return

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
                channel = client.get_channel(player['channel_id'])

                # Overall winner found, game ends
                if winner_found:
                    cardjitsuHandler.pay_players(winner, loser)
                    _ = databasequery.abandonMatch(username, force=True)
                    msg_id = await channel.fetch_message(player['message_id'])
                    await msg_id.delete()
                    await channel.send(content=f'GAME FINISHED. {winner} won!')

                # Just a round winner was declared
                else:
                    msg_id = await channel.fetch_message(player['message_id'])
                    await msg_id.delete()
                    if winner == loser:
                        msg_id = await channel.send(content=f'Round tied! Choose your next card, {player["_id"]}')
                    else:
                        msg_id = await channel.send(content=f'{winner} won that round! Choose your next card, {player["_id"]}')
                    msg_id = msg_id.id
                    gameCollection.update_one({'_id': player['_id']}, {'$set': {'message_id': msg_id}})

        else: await _update_window(username, 1)

    elif type == 'collect':
        if set_number != None:
            cardsToCollect = databasequery.collect(username, set_number, 'collect')
            await interaction.followup.send(cardsToCollect)
        else:
            await interaction.followup.send('Please Select a Pack Number!')

    elif type == 'collected':
        if set_number != None:
            cardsCollected = databasequery.collect(username, set_number, 'collected')
            await interaction.followup.send(cardsCollected)
        else:
            await interaction.followup.send('Please Select a Pack Number!')
    
    else:
        await interaction.followup.send("Failed To Execute Command!")

    if send_message:
        message = await interaction.followup.send('Boo')
        await message.delete()

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
    
    else:
        await interaction.followup.send("Please give a valid response!")

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
        players, _, _ = databasequery.player_lookup(username)

        for player in players:
            if player['_id'] != username:
                channel = client.get_channel(player['channel_id'])
                await channel.send(f'{username} has joined the game!')
                interaction_objects[interaction.user.name] = interaction

    await interaction.followup.send(joined)

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

@tree.command(name="test", description="This is a test function for DM's!")
async def _test(interaction):

    # Add To Interaction list when:
    #   User Creates/Joins a Game
    #   >>> interaction_objects[interaction.user.name] = interaction
    await interaction.response.send_message(interaction_objects)

    # async def edit_message(content):
    #     interaction = interaction_objects['mathidiot']
    #     await interaction.edit_original_response(content=content, view=view)

    # style = discord.ButtonStyle.blurple

    # one =   discord.ui.Button(style=style, emoji = '<:Card_Jitsu_1:895560920976207882>', label='1')
    # two =   discord.ui.Button(style=style, emoji = '<:Card_Jitsu_2:895560935018733608>', label='2')
    # three = discord.ui.Button(style=style, emoji = '<:Card_Jitsu_3:895560944145555476>', label='3')
    # four =  discord.ui.Button(style=style, emoji = '<:Card_Jitsu_4:895560953121357835>', label='4')
    # five =  discord.ui.Button(style=style, emoji = '<:Card_Jitsu_5:895560961367351297>', label='5')

    # one.callback =   lambda _: edit_message('Card 1 <:Card_Jitsu_1:895560920976207882>')
    # two.callback =   lambda _: edit_message('Card 2 <:Card_Jitsu_2:895560935018733608>')
    # three.callback = lambda _: edit_message('Card 3 <:Card_Jitsu_3:895560944145555476>')
    # four.callback =  lambda _: edit_message('Card 4 <:Card_Jitsu_4:895560953121357835>')
    # five.callback =  lambda _: edit_message('Card 5 <:Card_Jitsu_5:895560961367351297>')

    # view = discord.ui.View()
    # view.add_item(item=one)
    # view.add_item(item=two)
    # view.add_item(item=three)
    # view.add_item(item=four)
    # view.add_item(item=five)

    # await interaction.response.send_message("Press it you wont", view=view)

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