from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as soup
import csv

# my_url = 'https://clubpenguin.fandom.com/wiki/List_of_Card-Jitsu_Power_Cards'
# my_url = 'https://clubpenguin.fandom.com/wiki/List_of_Regular_Card-Jitsu_Cards_(series_1-4)'
my_url = 'https://clubpenguin.fandom.com/wiki/List_of_Regular_Card-Jitsu_Cards_(series_5-8)'

# opening up connection, grabbing the page

uClient = uReq(my_url)
page_html = uClient.read()
uClient.close()

# html parsing
page_soup = soup(page_html, "html.parser")

# Gravs each product
containers = page_soup.findAll("a", {'class': 'image'})

allElements = []

for i in containers:
    # if "Card-Jitsu" in i["href"] or 'card_image' in i['href']:
    allElements.append(i["href"])

with open('allCards.csv', 'r+') as file:
    writer = csv.writer(file)
    for i in allElements:
        writer.writerow([i])