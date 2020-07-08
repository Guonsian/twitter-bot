import random
import logging
import asyncio
from asgiref.sync import async_to_sync, sync_to_async


class Data(object):
	list = []

	set = "SET"
	get = "GET"
	extract = "EXTRACT"
	shuffle = "SHUFFLE"
	get_list = "GET_LIST"
	length = "LENGTH"
	insert = "INSERT"
	insert_last = "INSERT_LAST"

	def __init__(self, text, img=None):
		self.text = text.strip()
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

	@staticmethod
	def create_from_dict(dict):
		text = dict["text"]
		img = dict["image"]
		return Data(text, img)

	@staticmethod
	@async_to_sync
	async def access_list(mode, info=None):
		if mode == Data.set:
			if info is not None:
				Data.list = info
				logging.info("Saved the tweet list")
		elif mode == Data.get:
			logging.info("Returned the first element of the list")
			return Data.list[0]
		elif mode == Data.extract:
			first = Data.list[0]
			del Data.list[0]
			logging.info("Extracted the first element of the list")
			return first
		elif mode == Data.shuffle:
			if len(Data.list) > 1:
				Data.list = random.sample(Data.list, len(Data.list))
				print("Shuffled!")
				logging.info("Tweet list was shuffled")
			else:
				print("There aren't enough tweets to shuffle")
				logging.warning("There aren't enough tweets to shuffle")
		elif mode == Data.get_list:
			logging.info("Returned the whole list")
			return Data.list
		elif mode == Data.length:
			logging.info("Returned the length of the list")
			return len(Data.list)
		elif mode == Data.insert:
			if info is not None:
				logging.info("Inserting tweet to the list")
				Data.list.insert(0, info)
		elif mode == Data.insert_last:
			if info is not None:
				logging.info("Inserting (append) tweet to the list")
				Data.list.append(info)
