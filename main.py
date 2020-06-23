import os
import re
import time
import wget
import random
import shutil
import tweepy
import datetime
import threading
import load_module
from configparser import ConfigParser

path = os.path.dirname(__file__)
if len(path) > 0:
	os.chdir(path)


# Class Tweet: it's a thread that tweets every 1200 or 1800 seconds
class Tweet(threading.Thread):
	next = None
	hadTweet = False

	# Default values (this will be replaced from the config.ini):
	delay = 10
	delay_without_tweets = 1000
	intervals = [1200, 1800]

	def run(self):
		global tuits
		print("Tweet printer: Starting thread")
		Tweet.hadTweet = False

		now = datetime.datetime.now()  # get a datetime object containing current date and time
		next_time = (now + datetime.timedelta(0, Tweet.delay)).strftime(
			"%H:%M:%S")  # Get the time when the next tweet will be post, and format it to make it easier to read in the console
		Tweet.set_next_tweet_t(next_time)
		# Wait some seconds to avoid
		time.sleep(Tweet.delay)

		self.tweet()

	def tweet(self):
		global tuits
		global t

		if len(tuits) == 0:
			print("¡Se acabaron los tuits!")
			save()
			# Intentandolo en 1000 segundos
			t = threading.Timer(Tweet.delay_without_tweets, self.tweet)
			t.start()

			Tweet.hadTweet = True
			return

		to_tweet = tuits[0]  # get the first tweet
		del tuits[0]  # The item that to be displayed will be deleted

		if len(to_tweet.text) <= 280:  # Less than 281 chars
			print("To tweet:\n" + to_tweet.text)
			print("------------------------------------------------------------")
			try:
				print("Trying to tweet...")
				global api
				if to_tweet.img is not None:
					print(to_tweet.img)
					media = []
					if isinstance(to_tweet.img, list):
						for imagen in to_tweet.img:
							print("Uploading", imagen)
							media.append(api.media_upload(imagen).media_id)
						print("Trying to post tweet with several images")
						api.update_status(media_ids=media, status=to_tweet.text)
					else:
						print("Uploading", to_tweet.img)
						api.update_with_media(to_tweet.img, to_tweet.text)
				else:
					pass
					api.update_status(to_tweet.text)
			except:
				print("Something went wrong")
				print("------------------------------------------------------------")
				self.tweet()
			else:
				print("Tweeted!", end=" ")
				y = random.randint(Tweet.intervals[0], Tweet.intervals[1])

				now = datetime.datetime.now()  # get a datetime object containing current date and time
				next_time = (now + datetime.timedelta(0, y)).strftime(
					"%H:%M:%S")  # Get the time when the next tweet will be post, and format it to make it easier to read in the console
				Tweet.set_next_tweet_t(next_time)

				print("Next tweet in:", y, "seconds at " + str(next_time) + ". Remaining tuits:", len(tuits))
				print("------------------------------------------------------------")

				t = threading.Timer(y, self.tweet)
				t.start()

				Tweet.hadTweet = True  # Flag para indicar que se ha tweeteado y que se puede cancelar el proceso del timer

		else:
			print("That tweet couldn't be printed!")
			print("------------------------------------------------------------")
			self.tweet()

	def new():
		tw = Tweet()
		tw.daemon = True
		tw.start()

	def get_next_tweet_t():
		return Tweet.next

	def set_next_tweet_t(next_time):
		Tweet.next = next_time

	def get_had_tweet():
		return Tweet.hadTweet


class MDListener(threading.Thread):
	# Default values (this will be replaced from the config.ini):
	lastID = 0
	permited_ids = []
	read_md = 120
	read_md_timeout = 240

	def run(self):
		global api

		if MDListener.lastID == 0:
			print("Recovering the last MD... (because lastID=0)")
			try:
				last_dm = api.list_direct_messages()[
					0]  # We recover the last MD, and get its ID, after the first time to run the bot, this won't be used

				MDListener.lastID = last_dm.id
				print("LastID =", MDListener.lastID)
				self.save_last_dm()

			except Exception as e:
				print("Error while trying to get the newest MD: ", e)

		t = threading.Timer(120, self.search)
		t.start()

	def search(self):

		try:
			last_dms = api.list_direct_messages()
		except Exception as e:
			print("Error:", e)
			t = threading.Timer(240, self.search)
			t.start()
		else:
			for messages in last_dms:
				if int(messages.id) <= int(MDListener.lastID):
					break
				if 'message_data' in messages.message_create:
					text = messages.message_create['message_data']['text']
					user = messages.message_create['sender_id']

					if user in self.permited_ids:
						print("\nLoad possible tweet")
						print(text, "from:", user)
						if user in self.permited_ids:
							try:
								import requests
								site = requests.get(text)
								load_tweet(site.url)
							except Exception as e:
								print("Error:", e)

			if len(last_dms) > 0:
				MDListener.lastID = last_dms[0].id
				self.save_last_dm()

			t = threading.Timer(120, self.search)
			t.start()

	def save_last_dm(self):
		config = ConfigParser()

		config.read('config.ini')
		config.set('general', 'last_dm', str(MDListener.lastID))

		with open('config.ini', 'w') as f:
			config.write(f)


def menu():
	global tuits
	time.sleep(1)  # A bit of delay to print properly the other initial messages of the other threads
	while True:
		print("------------------------------------------------------------")
		print("1. Print next tweet\t", end="\t")
		print("2. Enter the next tweet")
		print("3. Delete next tweet\t", end="\t")
		print("4. Save remaining tweets")
		print("5. Tweet next tweet\t", end="\t")
		print("6. When is next tweet")
		print("7. Copy a tweet (by url)", end="\t")
		print("8. Copy a tweet (by url & downloading pic) NOT WORKING")
		print("9. Shuffle list\t", end="\t\t")
		print("10. Reload configuration")
		print("11. Exit")
		print("------------------------------------------------------------")
		user_input = input()
		try:
			x = int(user_input)
			if x == 1:
				if len(tuits) > 0:
					print("------------------------------------------------------------\n")
					print(tuits[0])
				else:
					print("There are not tweets to display")
			if x == 2:
				tuits.insert(0, load_module.Data(input("Insert the next tweet:")))
			elif x == 3:
				if len(tuits) > 1:
					del tuits[0]
					print("The first tweet in line was deleted, the next one is:")
					print(tuits[0])
				elif len(tuits) == 1:
					del tuits[0]
					print("The last tweet was deleted")
				else:
					print("There are not tweets to delete")
			elif x == 4:
				save()
			elif x == 5:
				if Tweet.get_had_tweet():
					t.cancel()
					Tweet.new()
				else:
					print("Don't abuse this function, wait until the bot has tweet at least one tweet")
			elif x == 6:
				next_t = Tweet.get_next_tweet_t()
				if next_t is None:
					print("Bot just started, wait some seconds")
				else:
					print("Next tweet will be tweet at", Tweet.get_next_tweet_t())
			elif x == 7:
				url = input("Insert the URL of the tweet to copy: ")
				load_tweet(url)
			elif x == 8:
				url = input("Insert the URL of the tweet (and download images) to copy: ")
				load_tweet(url, True)
			elif x == 9:
				if len(tuits) > 1:
					tuits = random.sample(tuits, len(tuits))
					print("Shuffled!")
				else:
					print("There aren't enough tweets to shuffle")
			elif x == 10:
				load(True)
			elif x == 11:
				save()
				tuits = []
				exit()
		except ValueError:  # If not a number
			print("Wrong input")


def save():
	global tuits
	try:
		load_module.save_to_json(tuits)
		print("Tweets had been saved")
	except:
		print("Error while trying to save the tweets")


def load(just_config=False):
	if not just_config:
		global tuits
		tuits = load_module.load_tweets()

	print("--- Loaded configuration: ---")

	general_config = load_module.load_general_config()

	MDListener.lastID = general_config[0]
	print("Config: lastID:", general_config[0])

	Tweet.delay = general_config[1]
	print("Config: delay:", general_config[1])

	Tweet.delay_without_tweets = general_config[2]
	print("Config: delay without tweets:", general_config[2])

	Tweet.intervals = general_config[3]
	print("Config: intevarls of tweets:", str(general_config[3]))

	MDListener.read_md = general_config[4]
	print("Config: read DM interval:", general_config[4])

	MDListener.read_md_timeout = general_config[5]
	print("Config: read DM interval (by timeout):", general_config[5])

	MDListener.permited_ids = general_config[6]
	print("Config: permited IDs for MD:", str(general_config[6]), "\n")


def load_tweet(url, download=False):
	try:
		id = re.split("/", url)[-1]
		if id.find("?") > 0:
			id = id[:id.find("?")]
		status = api.get_status(id, tweet_mode="extended")
		api.create_favorite(id)
		print("Tweet with id:", id, "was faved")

		print(status.full_text)

		full_real_text = status.full_text
		if download:
			full_real_text = full_real_text.rsplit("https://t.co", 1)[0]

		media_files = []
		download_names = []

		if download:
			if 'media' in status.entities:
				for photo in status.extended_entities['media']:
					media_files.append(photo['media_url'])

		if 'user_mentions' in status.entities:
			for user in status.entities['user_mentions']:
				to_remove = "@" + user['screen_name']
				full_real_text = full_real_text.replace(to_remove, "")

		if len(media_files) == 0:
			tuits.insert(0, load_module.Data(full_real_text))
		else:
			print("To download: ")
			try:
				os.mkdir("images")
			except FileExistsError:
				pass

			for m in media_files:
				print(m)

			for media_file in media_files:
				name = wget.download(media_file)
				download_names.append(shutil.move(src=name, dst="images"))

			tuits.insert(0, load_module.Data(full_real_text, download_names))
	except Exception as e:
		print("Error while trying to get the tweet:", e)


def auth():
	print("Starting authentication of Twitter:")
	global api
	global auth

	# Reading from the config file
	config = ConfigParser()
	config.read('config.ini')

	api_key = config.get('auth', 'api_key')
	api_secret_key = config.get('auth', 'api_secret_key')
	access_token = config.get('auth', 'access_token')
	access_token_secret = config.get('auth', 'access_token_secret')

	auth = tweepy.OAuthHandler(api_key, api_secret_key)
	auth.secure = True
	auth.set_access_token(access_token, access_token_secret)

	# Creating the api object
	api = tweepy.API(auth)

	# Trying to verify creentials
	try:
		api.verify_credentials()
		print("Authentication OK")
	except:
		print("Error during authentication")
		exit()


# Authenticate to Twitter
auth()

# Loading and parsing of the tuits from a whatsapp chat conversation
load()

# Starting the thread to tweet
Tweet.new()
md = MDListener()
md.daemon = True
md.start()
# Executing the menu in the main thread
menu()