import json, sys, time, requests, datetime, random, logging
from pymongo import MongoClient
import progressbar # https://github.com/WoLpH/python-progressbar
import config # config.py


def entryExistsSteam(steamid, name, collection_oc):
	found = collection_oc.find({"$or": [{"steamId":str(steamid)}, {"name": str(name)}]}).count()
	if (found == 1):
		return True
	else:
		return False

def entryExistsId(id, collection_oc):
	found = collection_oc.find({"id":id}).count()
	if (found == 1):
		return True
	else:
		return False

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
		collection_oc.create_index("id", unique=True)
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
					"_id": "$appid",
					"name": {"$first": "$name"}
					}
				},
				{"$sample": {
					"size": 150
					}
				}
			])
			# convert cursor to Python list
			to_update = []
			appids = []
			for k,item in enumerate(names_cur):
				to_update.append(item['name'])
				appids.append(item['_id'])

		if (pbar):
			bar = progressbar.ProgressBar(max_value=len(to_update)).start()

		search_count = 0
		for i,name in enumerate(to_update):
			if (pbar):
				bar.update(i+1)

			try:
				# if we already have a record for that steamId, don't bother doing the search, we already have a link between
				# the OpenCritic 'id' and the 'appid'
				if (not entryExistsSteam(appids[i], to_update[i], collection_oc)):
					# OpenCritic Game API e.g.
					# https://api.opencritic.com/api/game/search?criteria=steel%20division%202R
					r = requests.get(requests.Request('GET', "https://api.opencritic.com/api/game/search", params={'criteria':name}).prepare().url)
					if (r.ok):
						search_count = search_count + 1
						data = r.json()

						for value in data:
							# we don't have an existing record, insert one
							if (not entryExistsId(value['id'], collection_oc)):
								oc = value
								# add current datetimestamp
								oc['date'] = datetime.datetime.utcnow()
								# remove "dist" value which shows proximity match via the search entry
								oc.pop('dist', None)
								collection_oc.insert_one(oc)
							#else:
								#logging.info("id: " + str(oc['id']) + " already exists in the database")
					else:
						logging.error("status code: " + str(r.status_code))
						logging.error("opencritic search name: " + name)

					# sleep for a bit, there's no information on API throttling
					time.sleep(2) #seconds
				#else:
					#logging.info("appid: " + appids[i] + " found already in OpenCritic as an entry")
			except Exception as e:
				logging.error(str(e) + " - name: " + str(name))

		if (pbar):
			bar.finish()
		
		logging.info("Searched for " + str(search_count) + " games in OpenCritic.")
		logging.info("Finished updating OpenCritic search via " + refresh_type)
	except Exception as e:
		logging.error(str(e))

if __name__== "__main__":
	# PARTIAL: run on a small random subset coming from our Steam games listing
	updateOpenCritic(refresh_type="PARTIAL", pbar=True)