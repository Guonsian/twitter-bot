import os
import json
import re
import random
import logging
from configparser import ConfigParser

# This a fiel to parse from the old txt system to the new one with json

CONST_BEGINNING_OF_TWEET = "------- THIS IS THE NEXT TWEET TO DISPLAY -------\n"
OG_FILE = "tw.txt"
REMAINING_FILE = "remaining.txt"
REMAINING_JSON = "remaining.json"


def old_load():
	global tuits
	try:
		# TODO: Remove (this doesn't make sense anymore)
		print("Deprecated (maintained for a few versions): Trying to load reamining txt file")
		file = open(REMAINING_FILE, "r", encoding="utf-8")
		if os.path.getsize(REMAINING_FILE) == 0:
			raise FileNotFoundError()

	except FileNotFoundError:
		print("Trying to load original file")
		try:
			file = open(OG_FILE, "r", encoding="utf-8")
		except FileNotFoundError:
			print("You must have a " + OG_FILE + " or a " + REMAINING_FILE + " file in the same directory")
			logging.error("Couldn't fine a file to open and recover tweets")
			exit()

		content = file.read()
		tuits_in_order = re.split("[0-9]+/[0-9]+/[0-9]+ [0-9]+:[0-9]+ - [a-zA-Z0-9]+:", content)
		tuits = random.sample(tuits_in_order, len(tuits_in_order))
		print("Loaded from", OG_FILE)
	else:
		content = file.read()
		tuits = re.split(CONST_BEGINNING_OF_TWEET, content)
		del tuits[0]  # it's just an empty statement
		print("Loaded from", REMAINING_FILE)

	return tuits


def parse_to_json(t):
	file = open(REMAINING_JSON, "w+", encoding="utf-8")
	logging("Parsing tweets to: "+ REMAINING_JSON)

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


def save_to_json(t):
	with open(REMAINING_JSON, "w+", encoding="utf-8") as file:
		new_t = []
		for i in t:
			new_t.append(i.get_dict())
		file.write(json.dumps(new_t, indent=4, sort_keys=True))
		logging.info("Saving data to JSON")


class Data(object):

	def __init__(self, text, img=None):
		self.text = text
		self.img = img

	def get_dict(self):
		return {"text": self.text, "image": self.img}

	def __str__(self):
		if self.img is None:
			return "Tweet: " + self.text
		else:
			if isinstance(self.img, list):
				string = "Tweet: " + self.text + "\nImages:"
				for image in self.img:
					string = string + " " + image
				return string
			else:
				return "Tweet: " + self.text + "\nImage: " + self.img

	def create_from_dict(dict):
		text = dict["text"]
		img = dict["image"]
		return Data(text, img)


# This is the main function of this file, it retuns a list of Data objetcs
def load_tweets():
	tuits = load_from_json()
	if tuits is None:
		old_tuits = old_load()
		# Save the files as a JSON
		parse_to_json(old_tuits)
		# Load from that JSON
		tuits = load_from_json()

	logging.info("Loaded: " + str(len(tuits)) + " tweets")
	print("Loaded", len(tuits), "tweets")
	print("Success!\n")

	return tuits


def load_general_config():
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

		permited_ids = config.get('general', 'permited_ids').split(',')
		configuration_values.append(permited_ids)

	except Exception as e:
		print(e)
		print("Error trying to get the values from config.ini, the program will use the default values")
		configuration_values = [0, 10, 100, [1200, 1800], 120, 240, []]
		logging.warning("Couldn't get the configuration from the config.ini file")
		logging.warning(str(e))

	return configuration_values
