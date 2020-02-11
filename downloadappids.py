import json, sys, time, requests, datetime
import logging as log
import logging.handlers as handlers
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
import progressbar # https://github.com/WoLpH/python-progressbar
import config # config.py
import common # common.py

def downloadAllAppIDs(pbar=False):
	try:
		logging = common.setupLogging(log, handlers, sys)

		logging.info("Downloading All AppIDs")

		# downloads a list of every appid and name from the API
		# and stores in MongoDB collection

		client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)
		db = client['steam']
		collection = db['apps']
	
		r = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v0002/")

		if (r.ok):
			data = r.json()

			# create an index for appid, this vastly improves performance
			collection.create_index("appid", unique=True)

			if (pbar):
				bar = progressbar.ProgressBar(max_value=len(data['applist']['apps'])).start()

			requests_list = []
			for i,app in enumerate(data['applist']['apps']):
				if (pbar):
					bar.update(i+1)
				#UpdateOne will keep whatever information already exists
				requests_list.append(UpdateOne({'appid': int(app['appid'])}, {'$set': app}, upsert=True))
				# do bulk writes in batches, instead of one at a time
				if (i % 1000 == 0 or i+1 == len(data['applist']['apps'])):
					try:
						collection.bulk_write(requests_list)
						requests_list = []
					except BulkWriteError as bwe:
						logging.error(bwe)
			if (pbar):
				bar.finish()
			logging.info("Finished downloading AppIDs.")
			logging.info("Downloaded: " + common.sizeof_fmt(len(r.content)))
		else:
			logging.error("status code: " + str(r.status_code))
	except Exception as e:
		logging.error(str(e))

if __name__== "__main__":
    downloadAllAppIDs(pbar=True)