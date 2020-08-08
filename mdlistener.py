import auth
import tweepy
import logging
import threading
import load_module
from data import Data
from configparser import ConfigParser


timer_dm = None
api = None
favorites = []

class MDListener(threading.Thread):
	# Default values (this will be replaced from the config.ini):
	lastID = 0
	permitted_ids = []
	read_dm = 120
	read_dm_timeout = 240

	def run(self):
		global api
		global timer_dm

		api = auth.get_api()

		try:
			global favorites
			temp_fav = api.favorites()
			for fav in temp_fav:
				favorites.append(fav.id)
			logging.info("Loaded the last " + str(len(favorites)) + " fav tweets")
		except Exception as e:
			print("Error while trying to get the last favorites tweets: ", e)
			logging.warning("Couldn't recover the last favorites tweets: " + str(e))

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

			timer_dm = threading.Timer(MDListener.read_dm, self.search)
			logging.info("Starting timer to the first DM search")
			timer_dm.start()
		else:
			logging.info("Starting search")
			self.search()

	def search(self):
		global timer_dm
		global favorites
		try:
			new_favs = api.favorites()
			for fav in new_favs:
				if fav.id not in favorites:
					load_module.load_new_tweet("https://twitter.com/i/status/" + str(fav.id), from_fav=True)
					logging.info("Loaded tweet with id:" + str(fav.id))
			favorites = []
			for fav in new_favs:
				favorites.append(fav.id)
		except Exception as e:
			print("Error trying to get the last favs:", e)
			logging.warning("Couldn't recover the last favs: " + str(e))


		try:
			last_dms = [] # api.list_direct_messages()
			logging.debug("Getting the last DMs")
		except Exception as e:
			print("Error trying to get the last DMs:", e)
			logging.warning("Couldn't recover the DM list :" + str(e))
			timer_dm = threading.Timer(MDListener.read_dm_timeout, self.search)
			logging.info("Starting timer to the next DM search (with extended timeout)")
			timer_dm.start()
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
								if text[0:5] == "text:" or text[0:5] == "Text:":
									Data.access_list(mode=Data.insert, info=Data(text[5:].strip()))
									logging.info("Inserted next tweet")
								else:
									import requests
									site = requests.get(text)
									load_module.load_new_tweet(site.url)

							except Exception as e:
								print("Error:", e)
								logging.error("Error recovering the tweet: " + str(e))
					else:
						logging.warning("Not authorized person sent a DM to the bot")

			if len(last_dms) > 0:
				if int(last_dms[0].id) > int(MDListener.lastID):
					MDListener.lastID = last_dms[0].id
					self.save_last_dm()

			timer_dm = threading.Timer(MDListener.read_dm, self.search)
			logging.debug("Starting timer to the next DM search")
			timer_dm.start()

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
