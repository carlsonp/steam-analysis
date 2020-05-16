import json, sys, time, requests, datetime, random
import logging as log
import logging.handlers as handlers
from pymongo import MongoClient
import progressbar # https://github.com/WoLpH/python-progressbar
import config # config.py
import common # common.py

def getSteamId(name, collection_apps):
	found = collection_apps.find_one({'name':name})
	if (found and found['appid']):
		return found['appid']
	else:
		return None

def getTwitchToken(logging):
	# https://dev.twitch.tv/docs/authentication/getting-tokens-oauth#oauth-client-credentials-flow
	params = {'client_id':config.twitch_client_id, 'client_secret':config.twitch_client_secret, 'grant_type':'client_credentials'}
	r = requests.post("https://id.twitch.tv/oauth2/token", params=params)
	if (r.ok):
		data = r.json()
		logging.info("Obtained Twitch access token, it expires in: " + str(datetime.timedelta(seconds=data['expires_in'])))
		return(data['access_token'])
	else:
		logging.error("status code: " + str(r.status_code))
		time.sleep(1)

def updateTwitchTopGames(refresh_type="TOP", pbar=False):
	try:
		logging = common.setupLogging(log, handlers, sys)
		
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

		access_token = getTwitchToken(logging)

		if (pbar):
			bar = progressbar.ProgressBar(max_value=int(top_x * num_streams)).start()

		bytes_downloaded = 0
		game_rank = 1 # for game rank/order returned via Twitch
		i = 1 # for progress bar
		while (i < top_x * num_streams):
			try:
				# Twitch Top Games
				# https://dev.twitch.tv/docs/api/reference/#get-top-games
				params = {'first':first_x}
				if i != 1:
					params = {'first':first_x, 'after':pagination}
				r = requests.get("https://api.twitch.tv/helix/games/top", headers={'Client-ID':config.twitch_client_id, 'Authorization':"Bearer "+access_token}, params=params)
				if (r.ok):
					if (int(r.headers['Ratelimit-Remaining']) < 4):
						logging.info("rate limit: " + r.headers['Ratelimit-Limit'])
						logging.info("rate limit remaining: " + r.headers['Ratelimit-Remaining'])
					data = r.json()
					bytes_downloaded = bytes_downloaded + len(r.content)
					if (data['pagination']['cursor']):
						pagination = data['pagination']['cursor']
					else:
						logging.error("Unable to find pagination cursor")
						break # out of while loop

					for value in data['data']:
						# add to our historical listing
						# https://dev.twitch.tv/docs/api/reference/#get-streams
						r_g = requests.get("https://api.twitch.tv/helix/streams", headers={'Client-ID': config.twitch_client_id, 'Authorization':"Bearer "+access_token}, params={'first':num_streams, 'game_id':int(value['id'])})
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
								if (pbar):
									bar.update(i)
								i = i + 1
						else:
							logging.error("status code: " + str(r.status_code))
							# check OAuth and tokens
							if (r_g.status_code == 401):
								sys.exit(1)

						game_rank = game_rank + 1
						# https://dev.twitch.tv/docs/api/guide/#rate-limits
						time.sleep(2) #seconds
				else:
					logging.error("status code: " + str(r.status_code))
					# check OAuth and tokens
					if (r.status_code == 401):
						sys.exit(1)

				# sleep for a bit
				# https://dev.twitch.tv/docs/api/guide/#rate-limits
				time.sleep(2) #seconds
				# in some cases, there aren't the max number of streams for a game, thus we can jump ahead
				i = int(game_rank * num_streams)
			except Exception as e:
				logging.error(str(e))
				time.sleep(1)

		if (pbar):
			bar.finish()
		
		logging.info("Finished updating Twitch top games via " + refresh_type)
		logging.info("Downloaded: " + common.sizeof_fmt(bytes_downloaded))
	except Exception as e:
		logging.error(str(e))
		time.sleep(1)

if __name__== "__main__":
	# TOP: run on the top X games on Twitch
	updateTwitchTopGames(refresh_type="TOP", pbar=True)