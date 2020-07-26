import json, sys, time, re, string, requests, datetime, logging, random
from pymongo import MongoClient, UpdateOne
import progressbar # https://github.com/WoLpH/python-progressbar
import config # config.py
import common # common.py

def steamReviews(pbar=False):
	try:
		logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
						filename='steam-analysis.log', level=logging.DEBUG)
		# set the logging level for the requests library
		logging.getLogger('urllib3').setLevel(logging.WARNING)
		logging.info("Running Steam Reviews")

		client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)

		db = client['steam']
		collection = db['apps']

		to_update =	collection.aggregate([
				{"$match": {"type": {"$in": ["game", "dlc"]}}},
				{"$sort": {"reviews.last_updated": 1}}, # oldest first
				{"$limit": 50},
				{"$project": {"appid": 1, "_id":0}}
			])

		to_update = ([item['appid'] for item in to_update])

		if (pbar):
			bar = progressbar.ProgressBar(max_value=len(to_update)).start()

		bytes_downloaded = 0
		for i,appid in enumerate(to_update):
			if (pbar):
				bar.update(i+1)

			#logging.info("Running on appid: " + str(appid))
			r = requests.get("https://store.steampowered.com/appreviewhistogram/"+str(appid)+"?l=english&review_score_preference=0")
			if (r.ok):
				bytes_downloaded = bytes_downloaded + len(r.content)

				data = r.json()['results']

				# add current datetimestamp
				data['last_updated'] = datetime.datetime.utcnow()

				# convert Epoch seconds to UTC time
				# https://stackoverflow.com/questions/1697815/how-do-you-convert-a-python-time-struct-time-object-into-a-datetime-object
				data['start_date'] = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(int(data['start_date']))))
				data['end_date'] = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(int(data['end_date']))))

				if ('recent_events' in data):
					for k, event in enumerate(data['recent_events']):
						data['recent_events'][k]['start_date'] = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(int(event['start_date']))))
						data['recent_events'][k]['end_date'] = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(int(event['end_date']))))

				if ('rollups' in data):
					for k, event in enumerate(data['rollups']):
						data['rollups'][k]['date'] = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(int(event['date']))))

				if ('recent' in data):
					for k, event in enumerate(data['recent']):
						data['recent'][k]['date'] = datetime.datetime.fromtimestamp(time.mktime(time.gmtime(int(event['date']))))

				#update_one will keep whatever information already exists
				collection.update_one({'appid': int(appid)}, {'$set': {'reviews': data}}, upsert=True)

				if (pbar):
					bar.update(i+1)
			else:
				logging.error("status code: " + str(r.status_code))

			time.sleep(1)

		if (pbar):
			bar.finish()
			logging.info("Finished downloading Steam reviews.")
			logging.info("Downloaded: " + common.sizeof_fmt(bytes_downloaded))

	except Exception as e:
		logging.error(str(e))
		time.sleep(3)

if __name__== "__main__":
	steamReviews(pbar=True)
