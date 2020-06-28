import os
import re
import time
import wget
import random
import shutil
import tweepy
import logging
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
		print("Tweet printer: Starting thread")
		logging.info("Starting thread to tweet")
		Tweet.hadTweet = False

		now = datetime.datetime.now()  # get a datetime object containing current date and time
		next_time = (now + datetime.timedelta(0, Tweet.delay)).strftime(
			"%H:%M:%S")  # Get the time when the next tweet will be post, and format it to make it easier to read in the console
		Tweet.set_next_tweet_t(next_time)
		# Wait some seconds to avoid spam
		time.sleep(Tweet.delay)

		self.tweet()

	def tweet(self):
		global tweets_list
		global t

		if len(tweets_list) == 0:
			print("We run out of Tweets!")
			logging.warning("There are no tweets")
			save()
			# Trying it again in Tweet.delay_without_tweets seconds
			t = threading.Timer(Tweet.delay_without_tweets, self.tweet)
			t.start()

			Tweet.hadTweet = True
			return

		to_tweet = tweets_list[0]  # get the first tweet
		del tweets_list[0]  # The item that to be displayed will be deleted

		if len(to_tweet.text) <= 280:  # Less than 281 chars
			print("To tweet:\n" + to_tweet.text)
			print("------------------------------------------------------------")
			logging.info("Tweeting: " + to_tweet.text)
			try:
				print("Trying to tweet...")
				global api
				if to_tweet.img is not None:
					print("Media: " + to_tweet.img)
					media = []
					if isinstance(to_tweet.img, list):
						for imagen in to_tweet.img:
							print("Uploading", imagen)
							media.append(api.media_upload(imagen).media_id)
							logging.info("Upload: " + imagen)
						api.update_status(media_ids=media, status=to_tweet.text)
						print("Tweet with pic/s published")
						logging.info("Tweet with pic/s published")
					else:
						print("Uploading", to_tweet.img)
						api.update_with_media(to_tweet.img, to_tweet.text)
						logging.info("Tweet with pic published")
				else:
					api.update_status(to_tweet.text)
					logging.info("Tweet published")
			except Excepction as e:
				print("Something went wrong")
				print("------------------------------------------------------------")
				logging.warning("Tweet couldn't be tweeted: " + str(e))
				self.tweet()
			else:
				print("Tweeted!", end=" ")
				y = random.randint(Tweet.intervals[0], Tweet.intervals[1])

				now = datetime.datetime.now()  # get a datetime object containing current date and time
				next_time = (now + datetime.timedelta(0, y)).strftime(
					"%H:%M:%S")  # Get the time when the next tweet will be post, and format it to make it easier to read in the console
				Tweet.set_next_tweet_t(next_time)

				print("Next tweet in:", y, "seconds at " + str(next_time) + ". Remaining tweets:", len(tweets_list))
				print("------------------------------------------------------------")
				logging.info("Tweeted successfully, next tweet at " + str(next_time))
				t = threading.Timer(y, self.tweet)
				t.start()

				Tweet.hadTweet = True  # Flag para indicar que se ha tweeteado y que se puede cancelar el proceso del timer

		else:
			print("That tweet couldn't be printed!")
			print("------------------------------------------------------------")
			logging.warning("Tweet to long to tweet")
			self.tweet()

	@staticmethod
	def new():
		tw = Tweet()
		tw.daemon = True
		tw.start()

	@staticmethod
	def get_next_tweet_t():
		return Tweet.next

	@staticmethod
	def set_next_tweet_t(next_time):
		Tweet.next = next_time

	@staticmethod
	def get_had_tweet():
		return Tweet.hadTweet


class MDListener(threading.Thread):
	# Default values (this will be replaced from the config.ini):
	lastID = 0
	permitted_ids = []
	read_dm = 120
	read_dm_timeout = 240

	def run(self):
		global api

		if int(MDListener.lastID) == 0:
			print("Recovering the last DM... (because lastID=0)")
			logging.info("Starting DM Listener")
			try:
				last_dm = api.list_direct_messages()[
					0]  # We recover the last MD, and get its ID, after the first time to run the bot, this won't be used

				MDListener.lastID = last_dm.id
				print("LastID =", MDListener.lastID)
				logging.info("New last DM recovered: " + MDListener.lastID)
				self.save_last_dm()

			except Exception as e:
				print("Error while trying to get the newest DM: ", e)
				logging.warning("Couldn't recover the last DM: " + str(e))

		t = threading.Timer(MDListener.read_dm, self.search)
		logging.info("Starting timer to the first DM search")
		t.start()

	def search(self):

		try:
			last_dms = api.list_direct_messages()
			logging.debug("Getting the last DMs")
		except Exception as e:
			print("Error:", e)
			logging.warning("Couldn't recover the DM list :" + str(e))
			t = threading.Timer(MDListener.read_dm_timeout, self.search)
			logging.info("Starting timer to the next DM search (with extended timeout)")
			t.start()
		else:
			for messages in last_dms:
				if int(messages.id) <= int(MDListener.lastID):
					break
				if 'message_data' in messages.message_create:
					text = messages.message_create['message_data']['text']
					user = messages.message_create['sender_id']

					if user in self.permitted_ids:
						print("\nLoad possible tweet")
						print(text, "from:", user)
						if user in self.permitted_ids:
							try:
								import requests
								site = requests.get(text)
								load_tweet(site.url)
							except Exception as e:
								print("Error:", e)
								logging.error("Error recovering the tweet: " + str(e))

			if len(last_dms) > 0:
				if int(last_dms[0].id) > int(MDListener.lastID):
					MDListener.lastID = last_dms[0].id
					self.save_last_dm()

			t = threading.Timer(MDListener.read_dm, self.search)
			logging.debug("Starting timer to the next DM search")
			t.start()

	@staticmethod
	def save_last_dm():
		try:
			config = ConfigParser()

			config.read('config.ini')
			config.set('general', 'last_dm', str(MDListener.lastID))
			logging.info("Updated the last DM: " + MDListener.lastID)

			with open('config.ini', 'w') as f:
				config.write(f)
		except Exception as e:
			logging.error("Error saving the last DM: " + str(e))


def menu():
	global tweets_list
	time.sleep(1)  # A bit of delay to print properly the other initial messages of the other threads
	logging.info("Started menu")
	while True:
		print("------------------------------------------------------------")
		print("1. Print next tweet\t", end="\t")
		print("2. Enter the next tweet")
		print("3. Delete next tweet\t", end="\t")
		print("4. Save remaining tweets")
		print("5. Tweet next tweet\t", end="\t")
		print("6. When is next tweet")
		print("7. Copy a tweet (by url)", end="\t")
		print("8. Shuffle list")
		print("9. Reload configuration\t", end="\t")
		print("10. Exit")
		print("------------------------------------------------------------")
		user_input = input()
		try:
			x = int(user_input)
			logging.info("User introduced " + str(x))
			if x == 1:
				if len(tweets_list) > 0:
					print("------------------------------------------------------------\n")
					print(tweets_list[0])
					logging.info("Printed next tweet")
				else:
					print("There are not tweets to display")
					logging.warning("No tweets to print")
			if x == 2:
				tweets_list.insert(0, load_module.Data(input("Insert the next tweet:")))
				logging.info("Inserted next tweet")
			elif x == 3:
				if len(tweets_list) > 1:
					del tweets_list[0]
					print("The first tweet in line was deleted, the next one is:")
					logging.info("Deleted the first tweet in line")
					print(tweets_list[0])
				elif len(tweets_list) == 1:
					del tweets_list[0]
					print("The last tweet was deleted")
					logging.info("Printed next tweet")
				else:
					print("There are not tweets to delete")
			elif x == 4:
				save()
			elif x == 5:
				if Tweet.get_had_tweet():
					logging.info("Canceling the timer of the next tweet")
					t.cancel()
					logging.info("Starting new Thread to make a new tweet")
					Tweet.new()
				else:
					print("Don't abuse this function, wait until the bot has tweet at least one tweet")
					logging.warning("User tried to cancel timer before the other thread tweeted something")
			elif x == 6:
				next_t = Tweet.get_next_tweet_t()
				if next_t is None:
					print("Bot just started, wait some seconds")
				else:
					logging.info("User recover the time of the next time: " + Tweet.get_next_tweet_t())
					print("Next tweet will be tweet at", Tweet.get_next_tweet_t())
			elif x == 7:
				url = input("Insert the URL of the tweet to copy: ")
				logging.info("User introduced " + url + " to copy a tweet")
				load_tweet(url)
			elif x == 8:
				if len(tweets_list) > 1:
					tweets_list = random.sample(tweets_list, len(tweets_list))
					print("Shuffled!")
					logging.info("Tweet list was shuffled")
				else:
					print("There aren't enough tweets to shuffle")
			elif x == 9:
				logging.info("User try to reload the configuration")
				load(True)
			elif x == 10:
				save()
				tweets_list = []
				logging.info("Exiting program")
				exit()
		except ValueError:  # If not a number
			print("Wrong input")


def save():
	global tweets_list
	try:
		load_module.save_to_json(tweets_list)
		print("Tweets had been saved")
		logging.info("Tweets were saved")
	except Exception as e:
		print("Error while trying to save the tweets")
		logging.error("Error: " + str(e))


def load(just_config=False):
	if not just_config:
		global tweets_list
		tweets_list = load_module.load_tweets()
		logging.info("Received the tweet list")

	print("--- Loading configuration: ---")

	general_config = load_module.load_general_config()

	MDListener.lastID = general_config[0]
	print("Config: lastID:", general_config[0])
	logging.info("Config: lastID: " + str(general_config[0]))

	Tweet.delay = general_config[1]
	print("Config: delay:", general_config[1])
	logging.info("Config: delay: " + str(general_config[1]))

	Tweet.delay_without_tweets = general_config[2]
	print("Config: delay without tweets:", general_config[2])
	logging.info("Config: delay without tweets: " + str(general_config[2]))

	Tweet.intervals = general_config[3]
	print("Config: intervals of tweets:", str(general_config[3]))
	logging.info("Config: intervals of tweets: " + str(general_config[3]))

	MDListener.read_dm = general_config[4]
	print("Config: read DM interval:", general_config[4])
	logging.info("Config: read DM interval: " + str(general_config[4]))

	MDListener.read_dm_timeout = general_config[5]
	print("Config: read DM interval (by timeout):", general_config[5])
	logging.info("Config: read DM interval (by timeout): " + str(general_config[5]))

	MDListener.permitted_ids = general_config[6]
	print("Config: permitted IDs for MD:", str(general_config[6]), "\n")
	logging.info("Config: permited IDs for MD: " + str(general_config[6]))

	logging.info("Configuration updated")


def load_tweet(url):
	try:
		id = re.split("/", url)[-1]
		if id.find("?") > 0:
			id = id[:id.find("?")]
		status = api.get_status(id, tweet_mode="extended")
		api.create_favorite(id)
		print("Tweet with id:", id, "was faved")

		logging.info("Tweet with id: " + id + " was faved")
		logging.info("Tweet text: " + status.full_text)

		json_log = open("json_log.txt", "a")
		json_log.write(str(status) + "\n\n")
		json_log.close()


		print(status.full_text)

		full_real_text = status.full_text


		media_files = []
		download_names = []
		download = False

		if 'media' in status.entities:
			download = True
			for photo in status.extended_entities['media']:
				if photo['type'] == 'photo':
					media_files.append(photo['media_url'])
					logging.info("Getting info of photo: " + photo['media_url'])
				else:
					logging.info("Get something that is not a photo: no download")
					download = False
					break

			if download:
				full_real_text = full_real_text.rsplit("https://t.co", 1)[0]
				logging.info("Download option enable: removing the last link (t.co)")

		if 'user_mentions' in status.entities:
			for user in status.entities['user_mentions']:
				to_remove = "@" + user['screen_name']
				full_real_text = full_real_text.replace(to_remove, "")
				logging.info("Removing: " + to_remove)

		if download is False:
			tweets_list.insert(0, load_module.Data(full_real_text))
			logging.info("Inserting tweet to the list")
		else:
			print("To download: ")
			try:
				os.mkdir("images")
				logging.info("Created images directory")
			except FileExistsError:  # If directory already exists
				pass

			for m in media_files:
				print(m)

			for media_file in media_files:
				name = wget.download(media_file)
				download_names.append(shutil.move(src=name, dst="images"))
				logging.info("Downloaded: " + name)

			print("\n") # Add a extra line
			tweets_list.insert(0, load_module.Data(full_real_text, download_names))
			logging.info("Inserting tweet (with images) to the list")
	except Exception as e:
		print("Error while trying to get the tweet:", e)
		logging.error(str(e))


def auth():
	print("Starting authentication of Twitter:")
	logging.info("Starting authentication of Twitter")
	global api
	global auth

	# Reading from the config file
	config = ConfigParser()
	config.read('config.ini')
	logging.info("Read the config.ini file")

	api_key = config.get('auth', 'api_key')
	api_secret_key = config.get('auth', 'api_secret_key')
	access_token = config.get('auth', 'access_token')
	access_token_secret = config.get('auth', 'access_token_secret')

	auth = tweepy.OAuthHandler(api_key, api_secret_key)
	auth.secure = True
	auth.set_access_token(access_token, access_token_secret)

	# Creating the api object
	api = tweepy.API(auth)
	logging.info("Create the api object")

	# Trying to verify credentials
	try:
		api.verify_credentials()
		print("Authentication OK")
		logging.info("Authentication was successful")
	except Exception as e:
		print("Error during authentication")
		logging.error("Error while trying to authenticate: " + str(e))
		exit()


def main():
	# Creating the logs directory
	if not os.path.isdir("logs"):
		os.mkdir("logs")  # Create the logs directory

	# Find the files in logs directory
	files = os.listdir("logs")

	# If one log has "lastest-" at its beginning
	for file in files:
		if "latest-" in file:
			shutil.move("logs" + os.sep + file, "logs" + os.sep + file.replace("latest-", ""))

	# Setting up the logging file
	now = datetime.datetime.now().strftime("%d-%m-%Y (%H_%M_%S)")
	log_file_name = "logs" + os.sep + "latest-log-" + str(now) + ".txt"
	format = "[%(asctime)-15s] %(levelname)s (%(funcName)s): %(message)s"

	logging.basicConfig(format=format, filename=log_file_name, level="INFO")
	# We don't want to display DEBUG information

	logging.info("Created log file: " + log_file_name)

	# Loading and parsing of the tuits from a whatsapp chat conversation
	load()

	# Authenticate to Twitter
	auth()

	# Starting the thread to tweet
	Tweet.new()
	md = MDListener()
	md.daemon = True
	md.start()

	# Executing the menu in the main thread
	menu()


if __name__ == "__main__":
	main()
