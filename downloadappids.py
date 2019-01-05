import json, sys, time, requests, datetime, logging
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
import progressbar # https://github.com/WoLpH/python-progressbar
import config # config.py

def downloadAllAppIDs(pbar=False):
	logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
						filename='steam-analysis.log', level=logging.DEBUG)
	# set the logging level for the requests library
	logging.getLogger('urllib3').setLevel(logging.WARNING)
	logging.info("Downloading All AppIDs")

	# downloads a list of every appid and name from the API
	# and stores in MongoDB collection

	client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)
	db = client['steam']
	collection = db['apps']

	r = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v0002/")
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

if __name__== "__main__":
    downloadAllAppIDs(pbar=True)