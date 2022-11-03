from PIL import Image, ImageDraw, ImageFont
import os
import discord

background = Image.open('./images/blue_control.png')

player1 = 'MATHIDIOT'
player2 = 'STABLECK'

# card_played = Image.open('./images/colorElements/Card-Jitsu_card_back.png')
draw = ImageDraw.Draw(background)
font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 30, encoding='unic')
draw.text((70, 555), player1, (0, 0, 0), font=font)
draw.text((1050 - 20*(len(player2) - 1), 555), player2, (0, 0, 0), font=font)
background.save('./images/VERSUS_CP.png')

# card_played = Image.open('./images/colorElements/Card-Jitsu_card_back.png')
# card_played.thumbnail((170, 170), Image.ANTIALIAS)
# background.paste(card_played, (660, 215), card_played)