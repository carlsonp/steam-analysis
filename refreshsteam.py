import json, sys, time, requests, datetime, random, logging
from pymongo import MongoClient
import progressbar # https://github.com/WoLpH/python-progressbar
import config # config.py

def refreshSteamAppIDs(refresh_type="SAMPLING_GAMES", pbar=False):
	logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
						filename='steam-analysis.log', level=logging.DEBUG)
	# set the logging level for the requests library
	logging.getLogger('urllib3').setLevel(logging.WARNING)
	logging.info("Updating AppIDs via " + refresh_type)

	client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)
	client = MongoClient()
	db = client['steam']
	collection = db['apps']
	collection_hist = db['pricehistory']

	# create an index for appid, this vastly improves performance
	collection.create_index("appid", unique=True)
	collection.create_index("updated_date")

	# e.g.: CS Source
	# https://store.steampowered.com/api/appdetails?appids=240&cc=us&l=en

	# https://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI#Known_methods
	# https://stackoverflow.com/questions/13784059/how-to-get-the-price-of-an-app-in-steam-webapi

	try:
		to_update = []
		if (refresh_type == "FULL"):
			to_update = collection.distinct("appid", {})
		if (refresh_type == "ALL_NON_FAILURE" or refresh_type == "SAMPLING"):
			# see all appids that have had failures in descending order
			# db.getCollection('apps').find({"failureCount": {"$exists": true}}).sort({"failureCount":-1})
			# when the failureCount gets to 3 or higher, stop trying to pull data any more
			to_update = collection.distinct("appid", {
														"$or": [{"failureCount": {"$lt": 3}}, {"failureCount": {"$exists": False}}]
													})
		elif (refresh_type == "MISSING"):
			# count of missing entries
			# db.getCollection('apps').count({"updated_date": {"$exists": false}})
			to_update = collection.distinct("appid", {
														"updated_date": {"$exists": False},
														"$or": [{"failureCount": {"$lt": 3}}, {"failureCount": {"$exists": False}}]
													})
		elif (refresh_type == "GAMES" or refresh_type == "SAMPLING_GAMES"):
			to_update = collection.distinct("appid", {
														"type": {"$in": ["game", "dlc"]},
														"$or": [{"failureCount": {"$lt": 3}}, {"failureCount": {"$exists": False}}]
													})

		if (pbar):
			bar = progressbar.ProgressBar(max_value=len(to_update)).start()

		# shuffle the appids so we hit new ones each time
		random.shuffle(to_update) #in-place

		if (refresh_type == "SAMPLING" or refresh_type == "SAMPLING_GAMES"):
			# take only a small sampling of appids
			to_update = to_update[:100]

		for i,appid in enumerate(to_update):
			if (pbar):
				bar.update(i+1)
			data = requests.get("https://store.steampowered.com/api/appdetails?appids="+str(appid)+"&cc=us&l=en").json()

			for k,value in data.items():
				# for some reason, querying an appid sometimes yields a different number, e.g. 100 yields 80
				# it appears that "stale" records/appids can be re-pointed to existing working records
				if (value["success"] is True and appid == value['data']['steam_appid']):
					# rename "steam_appid" to "appid" so we insert properly into Mongo
					value['data']['appid'] = int(value['data'].pop('steam_appid'))
					# add current datetimestamp
					value['data']['updated_date'] = datetime.datetime.utcnow()
					try:
						# fix release_date -> date, change from string to ISODate() for Mongo
						value['data']['release_date']['date'] = datetime.datetime.strptime(value['data']['release_date']['date'], "%b %d, %Y")
					except ValueError as ve:
						logging.warning(ve)
						# do nothing, we couldn't parse the date
					# replace_one will completely replace the record, this is different than update_one
					collection.replace_one({'appid': int(value['data']['appid'])}, value['data'], upsert=True)

					if ('price_overview' in value['data']):
						# add a record to the price history since we grabbed it
						price_hist = value['data']['price_overview']
						# set the appid
						price_hist['appid'] = int(value['data']['appid'])
						# add current datetimestamp
						price_hist['date'] = datetime.datetime.utcnow()
						collection_hist.insert_one(price_hist)
				else:
					# increment the failure record count so we can start pruning off bad data
					collection.update_one({'appid': int(appid)}, {"$inc": {"failureCount":1}}, upsert=True)
					logging.info("Failed to get data for appid: " + str(appid) + " - incrementing failureCount.")
			# sleep for a bit, the API is throttled
			# limited to 200 requests every 5 minutes or so...
			# 10 requests every 10 seconds
			# 100,000 requests per day
			time.sleep(1.75) #seconds
		if (pbar):
			bar.finish()
		logging.info("Finished updating AppIDs via " + refresh_type)
	except Exception as e:
		logging.error(str(e))

if __name__== "__main__":
	# SAMPLING: run on a random sampling of 100 entries of any type
	# SAMPLING_GAMES: run on a random sampling of 100 games/dlc
	# FULL: do a full refresh of all entries, including those that have hit the failureCount limit in the past
	# ALL_NON_FAILURE: refresh all entries of any type that have not hit the failureCount limit
	# MISSING: only download records that do not have an entry in apps
	# GAMES: do a refresh of all games/dlc information already in the database
	refreshSteamAppIDs(refresh_type="SAMPLING_GAMES", pbar=True)