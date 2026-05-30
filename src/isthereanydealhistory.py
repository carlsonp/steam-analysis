import time, requests, datetime, os
from pymongo import MongoClient
import progressbar # https://github.com/WoLpH/python-progressbar
import common as common # common.py


def isthereanydealHistory(pbar=False):
	logging = common.setupLogging()
	try:
		logging.info("Updating isthereanydeal via pulling history")

		uri = f"mongodb://root:{os.environ['MONGODB_ROOT_PASSWORD']}@{os.environ['MONGODB_IP']}:{os.environ['MONGODB_PORT']}/"
		client = MongoClient(uri)
		db = client['steam']
		collection_hist = db['isthereanydealhistory']
		collection_itad = db['isthereanydeal']

		# create an index for id, this vastly improves performance
		collection_hist.create_index("id")
		collection_hist.create_index("date")
		collection_hist.create_index("appid")

		
		# take a sample of our isthereanydeal list
		# https://stackoverflow.com/questions/54440636/the-field-name-must-be-an-accumulator-object
		names_cur = collection_itad.aggregate([
			{"$sample": {
				"size":400
				}
			}
		])
		# convert cursor to Python list
		to_check = []
		for k,item in enumerate(names_cur):
			to_check.append(item['id'])

		if (pbar):
			bar = progressbar.ProgressBar(max_value=len(to_check)).start()

		bytes_downloaded = 0
		for i,check_id in enumerate(to_check):
			if (pbar):
				bar.update(i+1)

			try:
				insert_record = {}

				# https://docs.isthereanydeal.com/#tag/Game/operation/games-info-v2
				params = {
					'id': check_id,
					'key': os.environ['ISTHEREANYDEAL_API_KEY']
				}
				r = requests.get(requests.Request('GET', "https://api.isthereanydeal.com/games/info/v2", params=params, timeout=30).prepare().url)
				if (r.ok):
					data = r.json()
					bytes_downloaded = bytes_downloaded + len(r.content)

					insert_record = data

					# add current datetimestamp
					insert_record['date'] = datetime.datetime.now(datetime.UTC)

					# sleep for a bit, there is API throttling, 1000 requests every 5 minutes which is about 3 requests per second
					time.sleep(0.33) #seconds

					# https://docs.isthereanydeal.com/#tag/Waitlist-Stats/operation/stats-waitlist-v1
					params = {
						'id': check_id,
						'country': "US",
						'key': os.environ['ISTHEREANYDEAL_API_KEY']
					}
					r_second = requests.get(requests.Request('GET', "https://api.isthereanydeal.com/stats/waitlist/v1", params=params, timeout=30).prepare().url)
					if (r_second.ok):
						insert_record['waitlist_stats'] = r_second.json()

					else:
						logging.error("status code: " + str(r_second.status_code))
						time.sleep(1)
				
				else:
					logging.error("status code: " + str(r.status_code))
					time.sleep(1)

				# sleep for a bit, there is API throttling, 1000 requests every 5 minutes which is about 3 requests per second
				time.sleep(0.33) #seconds


				if insert_record:
					# insert into Mongo
					collection_hist.insert_one(insert_record)
				
			except Exception as e:
				logging.error(str(e) + " - id: " + str(check_id))
				time.sleep(1)

		if (pbar):
			bar.finish()

		logging.info("Finished updating isthereanydeal history")
		logging.info("Downloaded: " + common.sizeof_fmt(bytes_downloaded))
		common.writeBandwidth(db, bytes_downloaded)
	except Exception as e:
		logging.error(str(e))
		time.sleep(1)

if __name__== "__main__":
	isthereanydealHistory(pbar=True)
