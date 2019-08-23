import json, sys, time, requests, datetime, random, logging
from pymongo import MongoClient
import progressbar # https://github.com/WoLpH/python-progressbar
import config # config.py
import common # common.py

def updateOpenCritic(refresh_type="OLDEST", pbar=False):
	try:
		logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
							filename='steam-analysis.log', level=logging.DEBUG)
		# set the logging level for the requests library
		logging.getLogger('urllib3').setLevel(logging.WARNING)
		logging.info("Updating OpenCritic games via " + refresh_type)

		client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)
		client = MongoClient()
		db = client['steam']
		collection_oc = db['opencritic']

		# create an index for id, this vastly improves performance
		collection_oc.create_index("id", unique=True)
		collection_oc.create_index("date")
		collection_oc.create_index("steamId")

		# API page w/examples
        # https://api.opencritic.com/
	
		if (refresh_type == "OLDEST"):
			# find a sampling of OpenCritic IDs to work on ordered by date
			# will run on the oldest entries first
			names_cur = collection_oc.aggregate([
				{"$match": {}},
				{"$sort": {"date": 1}}, # oldest first
				{"$limit": 25},
				{"$project": {"id": 1, "_id":0}}
			])
			# convert cursor to Python list
			to_update = []
			for item in names_cur:
				to_update.append(item['id'])

		if (pbar):
			bar = progressbar.ProgressBar(max_value=len(to_update)).start()

		bytes_downloaded = 0
		for i,oc_id in enumerate(to_update):
			if (pbar):
				bar.update(i+1)

			try:
				# OpenCritic Game API e.g.
				# https://api.opencritic.com/api/game?id=7592
				r = requests.get(requests.Request('GET', "https://api.opencritic.com/api/game", params={'id':oc_id}).prepare().url)
				if (r.ok):
					data = r.json()
					bytes_downloaded = bytes_downloaded + len(r.content)

					oc = data
					# add current datetimestamp
					oc['date'] = datetime.datetime.utcnow()
					#update_one will keep whatever information already exists
					collection_oc.update_one({'id': int(oc['id'])}, {'$set': oc}, upsert=True)
				else:
					logging.error("status code: " + str(r.status_code))
					logging.error("opencritic game id: " + str(oc_id))
			except Exception as e:
				logging.error(str(e) + " - id: " + str(oc_id))

			# sleep for a bit, there's no information on API throttling
			time.sleep(2) #seconds

		if (pbar):
			bar.finish()
		logging.info("Finished updating OpenCritic games via " + refresh_type)
		logging.info("Downloaded: " + common.sizeof_fmt(bytes_downloaded))
	except Exception as e:
		logging.error(str(e))

if __name__== "__main__":
	# OLDEST: run on the oldest entries first
	updateOpenCritic(refresh_type="OLDEST", pbar=True)