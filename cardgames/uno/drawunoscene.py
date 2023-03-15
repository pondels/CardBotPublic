from PIL import Image, ImageDraw, ImageFont
import random

class DrawUnoScene():

    def __init__(self, players, names, hands, pile):
        self.background = Image.open('./images/pokertable.png')
        self.players = players
        self.names = names
        self.hands = hands
        self.pile = pile
        self.font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 45, encoding='unic')

    def update_window(self):
        if len(self.hands) == 2:
            self.south(  self.players[0], self.names[0], self.hands[0])
            self.north(  self.players[1], self.names[1], self.hands[1])
        if len(self.hands) == 3:
            self.south_west(self.players[0], self.names[0], self.hands[0])
            self.north(     self.players[1], self.names[1], self.hands[1])
            self.south_east(self.players[2], self.names[2], self.hands[2])
        if len(self.hands) == 4:
            self.south( self.players[0], self.names[0], self.hands[0])
            self.west(  self.players[1], self.names[1], self.hands[1])
            self.north( self.players[2], self.names[2], self.hands[2])
            self.east(  self.players[3], self.names[3], self.hands[3])
        if len(self.hands) == 5:
            self.south(     self.players[0], self.names[0], self.hands[0])
            self.south_west(self.players[1], self.names[1], self.hands[1])
            self.north_west(self.players[2], self.names[2], self.hands[2])
            self.north_east(self.players[3], self.names[3], self.hands[3])
            self.south_east(self.players[4], self.names[4], self.hands[4])
        if len(self.hands) == 6:
            self.south(     self.players[0], self.names[0], self.hands[0])
            self.south_west(self.players[1], self.names[1], self.hands[1])
            self.north_west(self.players[2], self.names[2], self.hands[2])
            self.north(     self.players[3], self.names[3], self.hands[3])
            self.north_east(self.players[4], self.names[4], self.hands[4])
            self.south_east(self.players[5], self.names[5], self.hands[5])
        if len(self.hands) == 7:
            self.south(     self.players[0], self.names[0], self.hands[0])
            self.south_west(self.players[1], self.names[1], self.hands[1])
            self.west(      self.players[2], self.names[2], self.hands[2])
            self.north_west(self.players[3], self.names[3], self.hands[3])
            self.north_east(self.players[4], self.names[4], self.hands[4])
            self.east(      self.players[5], self.names[5], self.hands[5])
            self.south_east(self.players[6], self.names[6], self.hands[6])
        if len(self.hands) == 8:
            self.south(     self.players[0], self.names[0], self.hands[0])
            self.south_west(self.players[1], self.names[1], self.hands[1])
            self.west(      self.players[2], self.names[2], self.hands[2])
            self.north_west(self.players[3], self.names[3], self.hands[3])
            self.north(     self.players[4], self.names[4], self.hands[4])
            self.north_east(self.players[5], self.names[5], self.hands[5])
            self.east(      self.players[6], self.names[6], self.hands[6])
            self.south_east(self.players[7], self.names[7], self.hands[7])

        self.draw_pile()
        self.background.save('./images/TableWithUno.png')

    def get_image(self, hand, card, show=False, rotation=None, size=(200, 200)):
        if show:
            listitems = hand[card]['thumbnail'].split('\\')
            card_color = listitems[-2]
            card_name = listitems[-1]
            card_played = Image.open(f'./cardgames/cards/unoCards/{card_color}/{card_name}')
        else: 
            card_played = Image.open(f'./cardgames/cards/unoCards/misc/unoBack.png')

        if rotation != None: card_played = card_played.rotate(rotation, expand=True)
        card_played.thumbnail(size, Image.ANTIALIAS)
        return card_played

    def paste_name(self, name, x, y, placement, rotation, color):
        size = self.font.getsize(name)
        name_image = Image.new('RGBA', (size[0] + 5, size[1] + 5))
        draw = ImageDraw.Draw(name_image)
        draw.text((5, 5), name, (75, 75, 75), font=self.font)
        draw.text((0, 0), name, color, font=self.font)
        rotated_name = name_image.rotate(rotation, expand=True)
        if placement == 'Horizontal': px, py = x - 12*len(name), y
        elif placement == 'Vertical': px, py = x, y - 12*len(name)
        elif placement == 'Diagonal': px, py = x - (rotated_name.size[0]/2).__ceil__(), y - (rotated_name.size[1]/2).__ceil__()
        sx, sy = rotated_name.size
        self.background.paste(rotated_name, (px, py, px+sx, py+sy), rotated_name)

    def draw_pile(self):

        # Drawing Face-Down Pile
        facedownpile = self.get_image('', '', show=False)
        self.background.paste(facedownpile, (725, 800), facedownpile)

        # Drawing The Pile
        listitems = self.pile['thumbnail'].split('\\')
        card_color = listitems[-2]
        card_name = listitems[-1]
        pile = Image.open(f'./cardgames/cards/unoCards/{card_color}/{card_name}')
        pile.thumbnail((200, 200), Image.ANTIALIAS)
        self.background.paste(pile, (885, 800), pile)

    def get_max_gap_regular(self, length):
        gap = 65 * (length-1)
        if gap > 180: return 180
        return gap

    def get_max_gap_diagonal(self, length):
        gap = 45 * (length-1)
        if gap > 125: return 125
        return gap

    # S
    def south(self, player, name, hand):
        for card in range(len(hand)):

            card_played = self.get_image(hand, card)

            middle = 825
            if len(hand) > 1:
                max_gap = self.get_max_gap_regular(len(hand))
                shift = int(round(max_gap / ((len(hand) - 1)/2), 0))
                self.background.paste(card_played, (middle - max_gap + card*shift, 1505), card_played)
            else: self.background.paste(card_played, (middle, 1505), card_played)

        color = (255, 255, 255)
        if player['is_turn']: color = (27, 205, 58)
        self.paste_name(name, x=870, y=1445, rotation=0, placement='Horizontal', color=color)
    # N
    def north(self, player, name, hand):
        for card in range(len(hand)):
            card_played = self.get_image(hand, card, rotation=180)
            
            middle = 825
            if len(hand) > 1:
                max_gap = self.get_max_gap_regular(len(hand))
                shift = int(round(max_gap / ((len(hand) - 1)/2), 0))
                self.background.paste(card_played, (middle + max_gap - card*shift, 85), card_played)
            else: self.background.paste(card_played, (middle, 85), card_played)

        color = (255, 255, 255)
        if player['is_turn']: color = (27, 205, 58)
        self.paste_name(name, x=870, y=300, rotation=180, placement='Horizontal', color=color)
    # E
    def east(self, player, name, hand):
        for card in range(len(hand)):
            card_played = self.get_image(hand, card, rotation=90)

            middlex = 1525
            middley = 835
            if len(hand) > 1:
                max_gap = self.get_max_gap_regular(len(hand))
                shift = int(round(max_gap / ((len(hand) - 1)/2), 0))
                self.background.paste(card_played, (middlex, middley + max_gap - card*shift), card_played)
            else: self.background.paste(card_played, (middlex, middley), card_played)

        color = (255, 255, 255)
        if player['is_turn']: color = (27, 205, 58)        
        self.paste_name(name, x=1460, y=875, rotation=90, placement='Vertical', color=color)
    # W
    def west(self, player, name, hand):
        for card in range(len(hand)):
            card_played = self.get_image(hand, card, rotation=270)

            middlex = 65
            middley = 830
            if len(hand) > 1:
                max_gap = self.get_max_gap_regular(len(hand))
                shift = int(round(max_gap / ((len(hand) - 1)/2), 0))
                self.background.paste(card_played, (middlex, middley - max_gap + card*shift), card_played)
            else: self.background.paste(card_played, (middlex, middley), card_played)

        color = (255, 255, 255)
        if player['is_turn']: color = (27, 205, 58)
        self.paste_name(name, x=280, y=885, rotation=270, placement='Vertical', color=color)
    # SE
    def south_east(self, player, name, hand):
        for card in range(len(hand)):
            card_played = self.get_image(hand, card, rotation=45, size=(220, 220))

            middlex = 1295
            middley = 1285
            if len(hand) > 1:
                max_gap = self.get_max_gap_diagonal(len(hand))
                shift = int(round(max_gap / ((len(hand) - 1)/2), 0))
                self.background.paste(card_played, (middlex - max_gap + card*shift, middley + max_gap - card*shift), card_played)
            else: self.background.paste(card_played, (middlex, middley), card_played)
            
        color = (255, 255, 255)
        if player['is_turn']: color = (27, 205, 58)
        self.paste_name(name, x=1300, y=1305, rotation=45, placement='Diagonal', color=color)
    # NW
    def north_west(self, player, name, hand):
        for card in range(len(hand)):
            card_played = self.get_image(hand, card, rotation=225, size=(220, 220))

            middlex = 265
            middley = 275
            if len(hand) > 1:
                max_gap = self.get_max_gap_diagonal(len(hand))
                shift = int(round(max_gap / ((len(hand) - 1)/2), 0))
                self.background.paste(card_played, (middlex + max_gap - card*shift, middley - max_gap + card*shift), card_played)
            else: self.background.paste(card_played, (middlex, middley), card_played)

        color = (255, 255, 255)
        if player['is_turn']: color = (27, 205, 58)
        self.paste_name(name, x=470, y=485, rotation=225, placement='Diagonal', color=color)
    # NE
    def north_east(self, player, name, hand):
        for card in range(len(hand)):
            card_played = self.get_image(hand, card, rotation=135, size=(220, 220))

            middlex = 1300
            middley = 285
            if len(hand) > 1:
                max_gap = self.get_max_gap_diagonal(len(hand))
                shift = int(round(max_gap / ((len(hand) - 1)/2), 0))
                self.background.paste(card_played, (middlex + max_gap - card*shift, middley + max_gap - card*shift), card_played)
            else: self.background.paste(card_played, (middlex, middley), card_played)
        
        color = (255, 255, 255)
        if player['is_turn']: color = (27, 205, 58)
        self.paste_name(name, x=1315, y=485, rotation=135, placement='Diagonal', color=color)
    # SW
    def south_west(self, player, name, hand):
        for card in range(len(hand)):
            card_played = self.get_image(hand, card, rotation=315, size=(220, 220))

            middlex = 275
            middley = 1280
            if len(hand) > 1:
                max_gap = self.get_max_gap_diagonal(len(hand))
                shift = int(round(max_gap / ((len(hand) - 1)/2), 0))
                self.background.paste(card_played, (middlex - max_gap + card*shift, middley - max_gap + card*shift), card_played)
            else: self.background.paste(card_played, (middlex, middley), card_played)
        
        color = (255, 255, 255)
        if player['is_turn']: color = (27, 205, 58)
        self.paste_name(name, x=485, y=1300, rotation=315, placement='Diagonal', color=color)

# players = [{'is_turn': True},
#            {'is_turn': False},
#            {'is_turn': False},
#            {'is_turn': False},
#            {'is_turn': False},
#            {'is_turn': False},
#            {'is_turn': False},
#            {'is_turn': False}
# ]

# names = [
#     'MATHIDIOT',
#     'STABLECK',
#     'LYRASAURUS ROSE',
#     'KUBRICSTAN',
#     'LOST ROBOT',
#     'MOONIEK',
#     'GAMERQUEEN',
#     'TOAST'
# ]

# cards = [
#     {'_id': 'greenplustwo', 'image': '<:greenplustwo:957750597900177409>', 'color': 'green', 'type': 'plustwo', 'thumbnail': 'cardgames\\cards\\unoCards\\greens\\greenplustwo.png'},
#     {'_id': 'greennine',    'image': '<:greennine:957750581005533214>',    'color': 'green', 'type': 9,         'thumbnail': 'cardgames\\cards\\unoCards\\greens\\greennine.png'},
#     {'_id': 'redsix',       'image': '<:redsix:957750667060072508>',       'color': 'red',   'type': 6,         'thumbnail': 'cardgames\\cards\\unoCards\\reds\\red6.png'},
#     {'_id': 'greenplustwo', 'image': '<:greenplustwo:957750597900177409>', 'color': 'green', 'type': 'plustwo', 'thumbnail': 'cardgames\\cards\\unoCards\\greens\\greenplustwo.png'},
#     {'_id': 'greennine',    'image': '<:greennine:957750581005533214>',    'color': 'green', 'type': 9,         'thumbnail': 'cardgames\\cards\\unoCards\\greens\\greennine.png'},
#     {'_id': 'redsix',       'image': '<:redsix:957750667060072508>',       'color': 'red',   'type': 6,         'thumbnail': 'cardgames\\cards\\unoCards\\reds\\red6.png'},
#     {'_id': 'greennine',    'image': '<:greennine:957750581005533214>',    'color': 'green', 'type': 9,         'thumbnail': 'cardgames\\cards\\unoCards\\greens\\greennine.png'},
#     {'_id': 'greeneight',   'image': '<:greeneight:957750572025540678>',   'color': 'green', 'type': 8,         'thumbnail': 'cardgames\\cards\\unoCards\\greens\\greeneight.png'},
#     {'_id': 'bluefive',     'image': '<:bluefive:957750519286345768>',     'color': 'blue',  'type': 5,         'thumbnail': 'cardgames\\cards\\unoCards\\blues\\bluefive.png'},
#     {'_id': 'bluefive',     'image': '<:bluefive:957750519286345768>',     'color': 'blue',  'type': 5,         'thumbnail': 'cardgames\\cards\\unoCards\\blues\\bluefive.png'}
# ]

# hands = [[random.choice(cards) for _ in range(random.randrange(2, 15))] for _ in range(len(names))]
# pile = {'_id': 'redsix', 'image': '<:redsix:957750667060072508>', 'color': 'red', 'type': 6, 'thumbnail': 'cardgames\\cards\\unoCards\\reds\\red6.png'}

# draw_scene_uno = DrawUnoScene(players, names, hands, pile)
# draw_scene_uno.update_window()
# draw_scene_uno.background.show()
# draw_scene_uno.background.save('./images/TableWithUno.png')