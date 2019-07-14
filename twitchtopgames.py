import json, sys, time, requests, datetime, random, logging
from pymongo import MongoClient
import progressbar # https://github.com/WoLpH/python-progressbar
import config # config.py


def getSteamId(name, collection_apps):
	found = collection_apps.find_one({'name':name})
	if (found and found['appid']):
		return found['appid']
	else:
		return None

def updateTwitchTopGames(refresh_type="TOP", pbar=False):
	try:
		logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
							filename='steam-analysis.log', level=logging.DEBUG)
		# set the logging level for the requests library
		logging.getLogger('urllib3').setLevel(logging.WARNING)
		logging.info("Updating Twitch top games via " + refresh_type)

		client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)
		client = MongoClient()
		db = client['steam']
		collection_twitchhistorical = db['twitchhistorical']
		collection_apps = db['apps']

		# create an index for id, this vastly improves performance
		collection_twitchhistorical.create_index("id")
		collection_twitchhistorical.create_index("date")
		collection_twitchhistorical.create_index("steamId")

		# API page w/examples
        # https://dev.twitch.tv/docs/api/

		# grab the top X number of games on Twitch
		top_x = 100
		# number of results to return in each top games request
		first_x = 50
		# number of streams to return for each game, max 100
		num_streams = 100

		if (pbar):
			bar = progressbar.ProgressBar(max_value=int(top_x * num_streams)).start()

		game_rank = 1 # for game rank/order returned via Twitch
		i = 1 # for progress bar
		while (i <= top_x * num_streams):
			try:
				# Twitch Top Games
				# https://dev.twitch.tv/docs/api/reference/#get-top-games
				params = {'first':first_x}
				if i != 1:
					params = {'first':first_x, 'after':pagination}
				r = requests.get("https://api.twitch.tv/helix/games/top", headers={'Client-ID':config.twitch_client_id}, params=params)
				if (r.ok):
					if (int(r.headers['Ratelimit-Remaining']) < 4):
						logging.info("rate limit: " + r.headers['Ratelimit-Limit'])
						logging.info("rate limit remaining: " + r.headers['Ratelimit-Remaining'])
					data = r.json()
					if (data['pagination']['cursor']):
						pagination = data['pagination']['cursor']
					else:
						logging.error("Unable to find pagination cursor")
						break # out of while loop

					for value in data['data']:
						# add to our historical listing
						r_g = requests.get("https://api.twitch.tv/helix/streams", headers={'Client-ID':config.twitch_client_id}, params={'first':num_streams, 'game_id':int(value['id'])})
						if (r_g.ok):
							if (int(r_g.headers['Ratelimit-Remaining']) < 4):
								logging.info("rate limit: " + r_g.headers['Ratelimit-Limit'])
								logging.info("rate limit remaining: " + r_g.headers['Ratelimit-Remaining'])
							data_g = r_g.json()
							for v in data_g['data']:
								v['date'] = datetime.datetime.utcnow()
								v.pop('thumbnail_url', None)
								v['name'] = value['name'] # pull the game name from our top games listing
								v['gamerank'] = game_rank
								appid = getSteamId(value['name'], collection_apps)
								if (appid):
									v['steamId'] = appid
								collection_twitchhistorical.insert_one(v)
								i = i + 1
								if (pbar):
									bar.update(i)

						game_rank = game_rank + 1
						# https://dev.twitch.tv/docs/api/guide/#rate-limits
						time.sleep(2) #seconds
				else:
					logging.error("status code: " + str(r.status_code))

				# sleep for a bit
				# https://dev.twitch.tv/docs/api/guide/#rate-limits
				time.sleep(2) #seconds
				# in some cases, we don't return the max number of streams for a game, thus we can jump ahead
				if (pbar):
					bar.update(int(game_rank * num_streams))
			except Exception as e:
				logging.error(str(e))

		if (pbar):
			bar.finish()
		
		logging.info("Finished updating Twitch top games via " + refresh_type)
	except Exception as e:
		logging.error(str(e))

if __name__== "__main__":
	# TOP: run on the top X games on Twitch
	updateTwitchTopGames(refresh_type="TOP", pbar=True)