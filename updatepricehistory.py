import json, sys, time, requests, datetime, random, logging
from pymongo import MongoClient
import progressbar # https://github.com/WoLpH/python-progressbar
import config # config.py

def updatePriceHistory(pbar=False):
	try:
		logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
							filename='steam-analysis.log', level=logging.DEBUG)
		# set the logging level for the requests library
		logging.getLogger('urllib3').setLevel(logging.WARNING)
		logging.info("Updating Price History")

		client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)
		client = MongoClient()
		db = client['steam']
		collection_hist = db['pricehistory']
		collection_apps = db['apps']

		# create an index for appid, this vastly improves performance
		collection_hist.create_index("appid")
		collection_hist.create_index("date")

		# e.g.: CS Source
		# https://store.steampowered.com/api/appdetails?appids=240&cc=us&l=en

		# https://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI#Known_methods
		# https://stackoverflow.com/questions/13784059/how-to-get-the-price-of-an-app-in-steam-webapi
	
		# find prices for all games and dlc
		to_update = collection_apps.distinct("appid", {"updated_date": {"$exists": True},
								"type": {"$in": ["game", "dlc"]},
								"is_free": False,
								"price_overview": {"$exists": True}
								})

		if (pbar):
			bar = progressbar.ProgressBar(max_value=len(to_update)).start()

		# shuffle the appids so we hit new ones each time
		random.shuffle(to_update) #in-place

		appids = []
		for i,appid in enumerate(to_update):
			appids.append(appid)
			if (pbar):
				bar.update(i+1)
			# run 20 or so at a time
			if ((i+1) % 20 == 0 or (i+1) == len(to_update)):
				try:
					# create a comma-delimited string of appids
					appids_str = ','.join(map(str, appids))
					# https://github.com/BrakeValve/dataflow/issues/5
					# e.g.
					# https://store.steampowered.com/api/appdetails?appids=662400,833310,317832,39150,830810,224540,931720,261900,431290,914410,812110,216464,826503,509681,71115,24679,231474,202452,863900,457100&cc=us&l=en&filters=price_overview
					r = requests.get("https://store.steampowered.com/api/appdetails?appids="+appids_str+"&cc=us&l=en&filters=price_overview")
					if (r.ok):
						data = r.json()

						for k,value in data.items():
							if (value["success"] is True):
								if (value['data']):
									price_hist = value['data']['price_overview']
									# set the appid based on the key
									price_hist['appid'] = int(k)
									# add current datetimestamp
									price_hist['date'] = datetime.datetime.utcnow()
									# remove formatted values, not needed
									# if they ever get added to the database, this will remove them
									# db.getCollection('pricehistory').update({},{"$unset": {"initial_formatted":1, "final_formatted":1, "currency":1}}, {multi: true})
									# and to validate that it worked, this should return nothing:
									# db.getCollection('pricehistory').find({"$or": [{"initial_formatted":{"$exists":true}}, {"final_formatted":{"$exists":true}}, {"currency":{"$exists":true}} ]})
									price_hist.pop('initial_formatted', None)
									price_hist.pop('final_formatted', None)
									price_hist.pop('currency', None)
									collection_hist.insert_one(price_hist)
								else:
									# No price_overview information returned, remove it from the entry
									# to prevent future unnecessary calls.  This is also an indicator
									# of stale app information.
									collection_apps.update_one({'appid': int(k)}, {"$unset": {"price_overview":""}})
									logging.info("No price information returned for appid: " + str(k) + " - clearing app price info.")
					else:
						logging.error("status code: " + str(r.status_code))
						logging.error("price history appids: " + appids_str)
				except Exception as e:
					logging.error(str(e) + " - appids: " + str(appids_str) + " - data: " + str(value))

				appids = []

				# sleep for a bit, the API is throttled
				# limited to 200 requests every 5 minutes or so...
				# 10 requests every 10 seconds
				# 100,000 requests per day
				time.sleep(1.75) #seconds

		if (pbar):
			bar.finish()
		logging.info("Finished updating price history.")
	except Exception as e:
		logging.error(str(e))

if __name__== "__main__":
	updatePriceHistory(pbar=True)