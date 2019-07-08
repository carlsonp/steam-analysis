import json, sys, time, requests, datetime, random, logging
from pymongo import MongoClient
import progressbar # https://github.com/WoLpH/python-progressbar
import config # config.py

def updateOpenCritic(refresh_type="PARTIAL", pbar=False):
	try:
		logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
							filename='steam-analysis.log', level=logging.DEBUG)
		# set the logging level for the requests library
		logging.getLogger('urllib3').setLevel(logging.WARNING)
		logging.info("Updating OpenCritic search via " + refresh_type)

		client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)
		client = MongoClient()
		db = client['steam']
		collection_oc = db['opencritic']
		collection_apps = db['apps']

		# create an index for id, this vastly improves performance
		collection_oc.create_index("id")
		collection_oc.create_index("date")
		collection_oc.create_index("steamId")

		# API page w/examples
        # https://api.opencritic.com/
	
		if (refresh_type == "PARTIAL"):
			# find appids for all games and dlc
			# https://stackoverflow.com/questions/54440636/the-field-name-must-be-an-accumulator-object
			names_cur = collection_apps.aggregate([
				{"$match": {"updated_date": {"$exists": True},
					"type": {"$in": ["game", "dlc"]},
					"failureCount": {"$exists": False}
					}
				},
				{"$group": {
					"_id": "$name"
					}
				},
				{"$sample": {
					"size": 200
					}
				}
			])
			# convert cursor to Python list
			to_update = []
			for item in names_cur:
				to_update.append(item['_id'])

		if (pbar):
			bar = progressbar.ProgressBar(max_value=len(to_update)).start()

		for i,name in enumerate(to_update):
			if (pbar):
				bar.update(i+1)

			try:
				# OpenCritic Game API e.g.
				# https://api.opencritic.com/api/game/search?criteria=steel%20division%202R
				r = requests.get(requests.Request('GET', "https://api.opencritic.com/api/game/search", params={'criteria':name}).prepare().url)
				if (r.ok):
					data = r.json()

					for value in data:
						oc = value
						# add current datetimestamp
						oc['date'] = datetime.datetime.utcnow()
						# remove "dist" value which shows proximity match via the search entry
						oc.pop('dist', None)
						#update_one will keep whatever information already exists
						collection_oc.update_one({'id': int(oc['id'])}, {'$set': oc}, upsert=True)
				else:
					logging.error("status code: " + str(r.status_code))
					logging.error("opencritic search name: " + name)
			except Exception as e:
				logging.error(str(e) + " - name: " + str(name))

			# sleep for a bit, there's no information on API throttling
			time.sleep(2) #seconds

		if (pbar):
			bar.finish()
		logging.info("Finished updating OpenCritic search via " + refresh_type)
	except Exception as e:
		logging.error(str(e))

if __name__== "__main__":
	# PARTIAL: run on a small random subset coming from our Steam games listing
	# MISSING: run on entries where we only have an 'id' and 'name' coming from the search
	updateOpenCritic(refresh_type="PARTIAL", pbar=True)