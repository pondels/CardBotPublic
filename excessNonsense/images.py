import cv2
from skimage import io
import pandas as pd

# METHOD #1: OpenCV, NumPy, and urllib
def url_to_image(url):
	filename = f'./images/{url.split("/")[7]}'
	# urllib.request.urlretrieve(url, filename, )
	width,height = 2340, 2640
	req = io.imread(url)
	cv2.imwrite(filename, cv2.cvtColor(cv2.resize(req, (width,height)), cv2.COLOR_RGBA2BGRA))

# initialize the list of image URLs to download
# urls = pd.read_csv('cardgames/cards/cardWebsites.csv')
# loop over the image URLs
# for url in urls['website']:
# 	image = url_to_image(url)

urls = [
	# 'https://static.wikia.nocookie.net/clubpenguin/images/7/7f/CJ_purple_card.png/revision/latest?cb=20150120045504',
	# 'https://static.wikia.nocookie.net/clubpenguin/images/f/f9/CJ_red_card.png/revision/latest?cb=20150120045341',
	# 'https://static.wikia.nocookie.net/clubpenguin/images/0/0e/CJ_blue_card.png/revision/latest?cb=20150120045400',
	# 'https://static.wikia.nocookie.net/clubpenguin/images/3/34/CJ_yellow_card.png/revision/latest?cb=20150120045423',
	# 'https://static.wikia.nocookie.net/clubpenguin/images/6/64/CJ_green_card.png/revision/latest?cb=20150120045446',
	# 'https://static.wikia.nocookie.net/clubpenguin/images/e/e8/CJ_orange_card.png/revision/latest?cb=20150120045454',
	# 'https://static.wikia.nocookie.net/clubpenguin/images/5/51/CJ_snow_icon.png/revision/latest?cb=20150120045256',
	# 'https://static.wikia.nocookie.net/clubpenguin/images/f/f2/CJ_fire_icon.png/revision/latest?cb=20150120045217',
	# 'https://static.wikia.nocookie.net/clubpenguin/images/6/64/CJ_water_icon.png/revision/latest?cb=20150120045243'
	'https://static.wikia.nocookie.net/clubpenguin/images/c/c3/Card-Jitsu_card_back.png/revision/latest?cb=20150307212151'
]
image = url_to_image(urls[0])