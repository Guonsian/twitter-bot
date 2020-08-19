import os
import re
import wget
import auth
import json
import shutil
import random
import logging
import mdlistener
from data import Data

from configparser import ConfigParser

OG_FILE = "tw.txt"
REMAINING_JSON = "remaining.json"


def old_load():
	print("Trying to load original file")
	try:
		file = open(OG_FILE, "r", encoding="utf-8")
	except FileNotFoundError:
		print("You must have a " + OG_FILE + " or a " + REMAINING_JSON + " file in the same directory")
		logging.error("Couldn't fine a file to open and recover tweets")
		exit()
	else:
		content = file.read()
		tweets_in_order = re.split("[0-9]+/[0-9]+/[0-9]+ [0-9]+:[0-9]+ - [a-zA-Z0-9]+:", content)
		tweets = random.sample(tweets_in_order, len(tweets_in_order))
		print("Loaded from", OG_FILE)

	return tweets


def parse_to_json(t):
	file = open(REMAINING_JSON, "w+", encoding="utf-8")
	logging("Parsing tweets to: " + REMAINING_JSON)

	new_t = []
	for i in t:
		aux = Data(i)
		new_t.append(aux.get_dict())

	text_file = json.dumps(new_t, indent=4, sort_keys=True)
	file.write(text_file)
	file.close()


def load_from_json():
	try:
		with open(REMAINING_JSON, "r", encoding="utf-8") as f:
			raw_data = json.load(f)
		data_list = []
		for i in raw_data:
			data_list.append(Data.create_from_dict(i))
		if len(data_list) == 0:
			print("Couldn't retrieve data from the .json")
			logging.warning("Couldn't retrieve data  JSON: " + REMAINING_JSON)
			return None
		print("Loaded from", REMAINING_JSON)
		logging.info("Loaded information from JSON: " + REMAINING_JSON)
		return data_list
	except:
		print("Error trying to load the .json")
		logging.warning("Couldn't load the JSON: " + REMAINING_JSON)
		return None


def save(output=False):
	try:
		save_to_json(Data.access_list(mode=Data.get_list))
		if output:
			print("Tweets had been saved")
		logging.info("Tweets were saved")
	except Exception as e:
		print("Error while trying to save the tweets")
		logging.error("Error: " + str(e))


# Saves the tweet list
def save_to_json(t):
	with open(REMAINING_JSON, "w+", encoding="utf-8") as file:
		new_t = []
		for i in t:
			new_t.append(i.get_dict())
		file.write(json.dumps(new_t, indent=4, sort_keys=True))
		logging.info("Saving data to JSON")


# This is the main function of this file, it retuns a list of Data objetcs
def load_tweets():
	tweets = load_from_json()
	if tweets is None:
		old_tweets = old_load()
		# Save the files as a JSON
		parse_to_json(old_tweets)
		# Load from that JSON
		tweets = load_from_json()

	logging.info("Loaded: " + str(len(tweets)) + " tweets")
	print("Loaded", len(tweets), "tweets")
	print("Success!\n")

	Data.access_list(mode=Data.set, info=tweets)


def load_general_config():
	if not os.path.isfile("config.ini"):
		logging.error("config.ini doesn't exist!")
		print("Config.ini doesn't exist, creating a new configuration file and loading default values")
		print("You will need to fill the auth values")

		open("config.ini", "a").close()  # Create a file: opening it and closing it

		config = ConfigParser()
		config.read("config.ini")
		logging.info("Created and open config.ini")

		config.add_section("auth")
		config.set("auth", "api_key", "")
		config.set("auth", "api_secret_key", "")
		config.set("auth", "access_token", "")
		config.set("auth", "access_token_secret", "")

		config.add_section("general")
		config.set("general", "last_dm", "0")
		config.set("general", "delay", "10")
		config.set("general", "delay_without_tweets", "100")
		config.set("general", "low_interval", "1200")
		config.set("general", "high_interval", "1800")
		config.set("general", "read_dm", "120")
		config.set("general", "read_dm_timeout", "240")
		config.set("general", "night_mode_extra_delay", "7200")
		config.set("general", "permited_ids", "")

		with open('config.ini', 'w') as f:
			config.write(f)

		logging.error("Exiting program: no fill values in config.ini")
		exit()
	try:
		config = ConfigParser()
		config.read('config.ini')
		logging.info("Open config.ini")

		configuration_values = []
		configuration_values.append(int(config.get('general', 'last_dm')))
		configuration_values.append(int(config.get('general', 'delay')))
		configuration_values.append(int(config.get('general', 'delay_without_tweets')))
		intervals = []
		intervals.append(int(config.get('general', 'low_interval')))
		intervals.append(int(config.get('general', 'high_interval')))
		configuration_values.append(intervals)

		configuration_values.append(int(config.get('general', 'read_dm')))
		configuration_values.append(int(config.get('general', 'read_dm_timeout')))

		configuration_values.append(int(config.get('general', 'night_mode_extra_delay')))

		permited_ids = config.get('general', 'permited_ids').split(',')
		configuration_values.append(permited_ids)

	except Exception as e:
		print(e)
		print("Error trying to get the values from config.ini, the program will use the default values")
		configuration_values = [0, 10, 100, [1200, 1800], 120, 240, 7200, []]
		logging.warning("Couldn't get the configuration from the config.ini file")
		logging.warning(str(e))

	return configuration_values


def load_new_tweet(url, from_fav=False):
	api = auth.get_api()

	try:
		id = re.split("/", url)[-1]
		if id.find("?") > 0:
			id = id[:id.find("?")]
		status = api.get_status(id, tweet_mode="extended")
		if id in mdlistener.favorites_list:
			return
		mdlistener.favorites_list.append(id)

		if not from_fav:
			api.create_favorite(id)
			print("Tweet with id:", id, "was faved")
			logging.info("Tweet with id: " + id + " was faved")
		else:
			print("Received fav with tweet id: " + str(id))
			logging.info("Received fav with tweet id: " + str(id))
			if 'user_mentions' in status.entities:
				if len(status.entities['user_mentions']) > 0:

					print("This could be an answer, so then this is not process\n")
					logging.info("This could be an answer, so then this is not process")
					print(status.full_text)
					logging.info("Tweet text: " + status.full_text)
					print("------------------------------------------------------------")
					return

		logging.info("Tweet text: " + status.full_text)

		print(status.full_text)

		full_real_text = status.full_text

		media_files = []
		download_names = []
		download = False

		if 'media' in status.entities:
			logging.info("Media found")
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
			if len(status.entities['user_mentions']) > 0:
				logging.info("User mentions found")
			for user in status.entities['user_mentions']:
				to_remove = "@" + user['screen_name']
				full_real_text = full_real_text.replace(to_remove, "")
				logging.info("Removing: " + to_remove)

		if download is False:
			logging.info("Trying to insert without download")
			if from_fav:
				Data.access_list(mode=Data.insert_random, info=Data(full_real_text))
			else:
				Data.access_list(mode=Data.insert, info=Data(full_real_text))

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

			print("\n")  # Add a extra line

			if from_fav:
				Data.access_list(mode=Data.insert_random, info=Data(full_real_text, download_names))
			else:
				Data.access_list(mode=Data.insert, info=Data(full_real_text, download_names))
			save()

		print("------------------------------------------------------------")

	except Exception as e:
		print("Error while trying to get the tweet:", e)
		logging.error(str(e))
