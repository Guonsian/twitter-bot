import os
import re
import time
import auth
import random
import tweepy
import logging
import datetime
import requests
import threading
import load_module
from data import Data

api = None

# Class Tweet: it's a thread that tweets every 1200 or 1800 seconds
class Tweet(threading.Thread):
	next = None
	hadTweet = False
	timer_tweet = None

	# Default values (this will be replaced from the config.ini):
	delay = 10
	delay_without_tweets = 1000
	intervals = [1200, 1800]
	night_mode_extra_delay = 7200

	# add one count every time it fails
	counter = 0

	def run(self):
		print("Tweet printer: Starting thread")
		logging.info("Starting thread to tweet")
		Tweet.hadTweet = False

		global api
		api = auth.get_api()

		now = datetime.datetime.now()  # get a datetime object containing current date and time
		next_time = (now + datetime.timedelta(0, Tweet.delay)).strftime(
			"%H:%M:%S")  # Get the time when the next tweet will be post, and format it to make it easier to read in the console
		Tweet.set_next_tweet_t(next_time)
		# Wait some seconds to avoid spam
		time.sleep(Tweet.delay)

		self.tweet()

	def tweet(self):

		if Data.access_list(mode=Data.length) == 0:
			print("We run out of Tweets!")
			logging.warning("There are no tweets")
			load_module.save(output=True)
			# Trying it again in Tweet.delay_without_tweets seconds
			Tweet.timer_tweet = threading.Timer(Tweet.delay_without_tweets, self.tweet)
			Tweet.timer_tweet.start()

			Tweet.hadTweet = True
			return

		try:
			to_tweet = Data.access_list(mode=Data.extract)

			if len(to_tweet.text) <= 280:  # Less than 281 chars

				print("To tweet:\n" + to_tweet.text)
				print("------------------------------------------------------------")
				logging.info("Tweeting: " + to_tweet.text)
				print("Trying to tweet...")

				append_url = None
				if len(to_tweet.text) > 1:
					try:
						if to_tweet.text.find("https://t.co/") != -1 and to_tweet.text.find("https://t.co/") != 0:
							p = re.split("https://t.co/", to_tweet.text)
							print(p)
							if len(p) == 2:
								to_tweet.text = p[0]
								append_url = requests.get("https://t.co/" + p[1]).url
								print(append_url)
							if len(p) == 1:
								to_tweet.text = ""
								append_url = requests.get("https://t.co/" + p[0]).url
								print(append_url)


					except Exception as e:
						print(e)

				if to_tweet.img is not None:
					print("Media: " + str(to_tweet.img))
					media = []
					if isinstance(to_tweet.img, list):
						for image in to_tweet.img:
							print("Uploading", image)
							media.append(api.media_upload(image).media_id)
							logging.info("Upload: " + image)

						api.update_status(media_ids=media, status=to_tweet.text, attachment_url=append_url)

						print("Tweet with pic/s published")
						logging.info("Tweet with pic/s published")
					else:  # Not used any more but legacy option just in case
						print("Uploading", to_tweet.img)
						api.update_with_media(to_tweet.img, to_tweet.text)
						logging.info("Tweet with pic published")
				else:
					api.update_status(status=to_tweet.text, attachment_url=append_url)

					logging.info("Tweet published")

				print("Tweeted!", end=" ")
				seconds_to_wait = random.randint(Tweet.intervals[0], Tweet.intervals[1])

				now = datetime.datetime.now()  # get a datetime object containing current date and time
				if now.hour in range(1, 9):
					seconds_until_end_of_night_mode = (now.replace(hour=9, minute=0, second=0, microsecond=0) - now).total_seconds()
					if seconds_until_end_of_night_mode < Tweet.night_mode_extra_delay:
						seconds_to_wait = seconds_to_wait + seconds_until_end_of_night_mode
					else:
						seconds_to_wait = seconds_to_wait + Tweet.night_mode_extra_delay

				next_time = (now + datetime.timedelta(0, seconds_to_wait)).strftime(
					"%H:%M:%S")  # Get the time when the next tweet will be post, and format it to make it easier to
				# read in the console
				Tweet.set_next_tweet_t(next_time)


				print("Next tweet in:", seconds_to_wait, "seconds at " + str(next_time) + ". Remaining tweets:",
					Data.access_list(mode=Data.length))
				print("------------------------------------------------------------")
				logging.info("Tweeted successfully, next tweet at " + str(next_time))
				Tweet.timer_tweet = threading.Timer(seconds_to_wait, self.tweet)
				Tweet.timer_tweet.start()
				Tweet.counter = 0

				Tweet.hadTweet = True  # Flag to indicate that it has tweeted and therefore, the timer can be cancelled
				load_module.save()

			else:
				print("That tweet couldn't be printed!")
				print("------------------------------------------------------------")
				logging.warning("Tweet to long to tweet")
				self.tweet()

		except Exception as e:
			logging.error("Tweet couldn't be tweeted: " + str(e))
			Tweet.counter = Tweet.counter + 1
			Data.access_list(mode=Data.insert_last, info=to_tweet)

			if Tweet.counter >= 5:
				print("5 times in a row a tweet couldn't be used, the program will exit")
				os._exit(1)
			else:
				print("Something went wrong trying to tweet, trying to tweet in 100/1000 seconds")
				print("------------------------------------------------------------")
				now = datetime.datetime.now()
				if now.hour in range(1, 9):
					time_to_wait = 1000
				else:
					time_to_wait = 100
				Tweet.timer_tweet = threading.Timer(time_to_wait, self.tweet)
				Tweet.timer_tweet.start()

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