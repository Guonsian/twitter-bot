import tweepy
import logging
from configparser import ConfigParser


def auth():
	print("Starting authentication of Twitter:")
	logging.info("Starting authentication of Twitter")

	# Reading from the config file
	config = ConfigParser()
	config.read('config.ini')
	logging.info("Read the config.ini file")

	api_key = config.get('auth', 'api_key')
	api_secret_key = config.get('auth', 'api_secret_key')
	access_token = config.get('auth', 'access_token')
	access_token_secret = config.get('auth', 'access_token_secret')

	auth_object = tweepy.OAuthHandler(api_key, api_secret_key)
	auth_object.secure = True
	auth_object.set_access_token(access_token, access_token_secret)

	# Creating the api object
	api = tweepy.API(auth_object)
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

	return api
