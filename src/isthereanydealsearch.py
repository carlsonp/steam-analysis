import time, requests, datetime, os
from pymongo import MongoClient
from rapidfuzz import fuzz # https://github.com/rapidfuzz/RapidFuzz
import progressbar # https://github.com/WoLpH/python-progressbar
import common as common # common.py

def entryExists(appid, collection_itad):
    found = collection_itad.count_documents(
        {"appid": str(appid)}
    )
    return found > 0

def isthereanydealSearch(pbar=False):
	logging = common.setupLogging()
	try:
		logging.info("Updating isthereanydeal via searching")

		uri = f"mongodb://root:{os.environ['MONGODB_ROOT_PASSWORD']}@{os.environ['MONGODB_IP']}:{os.environ['MONGODB_PORT']}/"
		client = MongoClient(uri)
		db = client['steam']
		collection_itad = db['isthereanydeal']
		collection_apps = db['apps']

		# create an index for id, this vastly improves performance
		collection_itad.create_index("id", unique=True)
		collection_itad.create_index("date")
		collection_itad.create_index("appid")

		
		# find appids for all games and dlc, take a sample
		# https://stackoverflow.com/questions/54440636/the-field-name-must-be-an-accumulator-object
		names_cur = collection_apps.aggregate([
			{"$match": {"updated_date": {"$exists": True},
				"type": {"$in": ["game", "dlc"]},
				"failureCount": {"$exists": False}
				}
			},
			{"$group": {
				"_id": "$appid",
				"name": {"$first": "$name"},
				"type": {"$first": "$type"},
				}
			},
			{"$sample": {
				"size":900
				}
			}
		])
		# convert cursor to Python list
		to_check = []
		for k,item in enumerate(names_cur):
			to_check.append({'appid': item['_id'], 'name': item['name'], 'type': item['type']})

		if (pbar):
			bar = progressbar.ProgressBar(max_value=len(to_check)).start()

		search_count = 0
		bytes_downloaded = 0
		for i,check in enumerate(to_check):
			if (pbar):
				bar.update(i+1)

			try:
				# if we already have a record for that appid, don't bother doing the search, we already have a link between
				# the isthereanydeal 'id' and the 'appid'
				if (not entryExists(check['appid'], collection_itad)):
					# https://docs.isthereanydeal.com/#tag/Lookup/operation/games-search-v1
					params = {
						'title': check['name'],
						'key': os.environ['ISTHEREANYDEAL_API_KEY']
					}
					r = requests.get(requests.Request('GET', "https://api.isthereanydeal.com/games/search/v1", params=params).prepare().url)
					if (r.ok):
						search_count = search_count + 1
						data = r.json()
						bytes_downloaded = bytes_downloaded + len(r.content)

						# make sure type is equal as well as fuzzy match on title
						if fuzz.ratio(data[0]['title'], check['name']) >= 0.85 and data[0]['type'] == check['type']:
							insertval = data[0]
							# add current datetimestamp
							insertval['date'] = datetime.datetime.now(datetime.UTC)
							# add appid
							insertval['appid'] = check['appid']
							# add steam name
							insertval['steam_name'] = check['name']
							# insert into Mongo
							collection_itad.insert_one(insertval)
						else:
							logging.info(f"{data[0]['title']} and {check['name']} don't seem to match up... skipping...")
					else:
						logging.error("status code: " + str(r.status_code))
						logging.error("isthereanydeal search: " + check['name'])

					# sleep for a bit, there is API throttling, 1000 requests every 5 minutes which is about 3 requests per second
					time.sleep(0.33) #seconds
				#else:
					#logging.info("appid: " + appids[i] + " found already in isthereanydeal as an entry")
			except Exception as e:
				logging.error(str(e) + " - name: " + str(check['name']))
				time.sleep(1)

		if (pbar):
			bar.finish()

		logging.info("Searched for " + str(search_count) + " games in isthereanydeal.")
		logging.info("Finished updating isthereanydeal search")
		logging.info("Downloaded: " + common.sizeof_fmt(bytes_downloaded))
		common.writeBandwidth(db, bytes_downloaded)
	except Exception as e:
		logging.error(str(e))
		time.sleep(1)

if __name__== "__main__":
	isthereanydealSearch(pbar=True)
