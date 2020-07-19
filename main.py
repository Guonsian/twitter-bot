import os
import re
import time
import auth
import random
import shutil
import tweepy
import logging
import datetime
import threading
import load_module
from data import Data
from tweet import Tweet
from mdlistener import MDListener
from configparser import ConfigParser

path = os.path.dirname(__file__)
if len(path) > 0:
	os.chdir(path)


def menu():
	time.sleep(1)  # A bit of delay to print properly the other initial messages of the other threads
	logging.info("Started menu")
	while True:
		print("------------------------------------------------------------")
		print("1. Print next tweet\t", end="\t")
		print("2. Enter the next tweet")
		print("3. Delete next tweet\t", end="\t")
		print("4. Put the tweet at the end of the queue")
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
				if Data.access_list(mode=Data.length) > 0:
					print("------------------------------------------------------------\n")
					print(Data.access_list(mode=Data.get))
					logging.info("Printed next tweet")
				else:
					print("There are not tweets to display")
					logging.warning("No tweets to print")
			if x == 2:
				Data.access_list(mode=Data.insert, info=Data(input("Insert the next tweet:")))
				load_module.save()
				logging.info("Inserted next tweet")
			elif x == 3:
				if Data.access_list(mode=Data.length) > 1:
					Data.access_list(mode=Data.extract)
					print("The first tweet in line was deleted, the next one is:")
					logging.info("Deleted the first tweet in line")
					print(Data.access_list(mode=Data.get))
					load_module.save()
				elif Data.access_list(mode=Data.length) == 1:
					Data.access_list(mode=Data.extract)
					print("The last tweet was deleted")
					logging.info("Printed next tweet")
					load_module.save()
				else:
					print("There are not tweets to delete")
			elif x == 4:
				if Data.access_list(mode=Data.length) > 1:
					Data.access_list(mode=Data.insert_last, info=Data.access_list(mode=Data.extract))
					print("Sent the first tweet in queue to the last position")
					logging.info("Sent the first tweet in queue to the last position")
					load_module.save()
			elif x == 5:
				if Tweet.get_had_tweet():
					logging.info("Canceling the timer of the next tweet")
					Tweet.timer_tweet.cancel()
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
				load_module.load_new_tweet(url)
			elif x == 8:
				Data.access_list(mode=Data.shuffle)
			elif x == 9:
				logging.info("User try to reload the configuration")
				load(True)
			elif x == 10:
				load_module.save(output=True)
				logging.info("Exiting program")
				exit()
		except ValueError:  # If not a number
			print("Wrong input")


def load(just_config=False):
	if not just_config:
		load_module.load_tweets()

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

	Tweet.night_mode_extra_delay = general_config[6]
	print("Config: read night mode extra delay:", general_config[6])
	logging.info("Config: read night mode extra delay: " + str(general_config[6]))

	MDListener.permitted_ids = general_config[7]
	print("Config: permitted IDs for MD:", str(general_config[7]), "\n")
	logging.info("Config: permitted IDs for MD: " + str(general_config[7]))

	logging.info("Configuration updated")


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

	logging.basicConfig(handlers=[logging.FileHandler(filename=log_file_name, encoding='utf-8', mode='a+')],
						format=format, level=logging.INFO)
	# We don't want to display DEBUG information

	logging.info("Created log file: " + log_file_name)

	# Loading and parsing of the tuits from a whatsapp chat conversation
	load()

	# Authenticate to Twitter
	auth.auth()

	# Starting the thread to tweet
	Tweet.new()
	md = MDListener()
	md.daemon = True
	md.start()

	# Executing the menu in the main thread
	menu()


if __name__ == "__main__":
	main()
