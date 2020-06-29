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

	@staticmethod
	def create_from_dict(dict):
		text = dict["text"]
		img = dict["image"]
		return Data(text, img)
