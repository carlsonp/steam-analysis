import time, re, requests, datetime, os
from pymongo import MongoClient
import progressbar # https://github.com/WoLpH/python-progressbar
import common as common # common.py

def steamTopGames(pbar=False):
    logging = common.setupLogging()
    try:
        logging.info("Running Steam Top Games")

        uri = f"mongodb://root:{os.environ['MONGODB_ROOT_PASSWORD']}@{os.environ['MONGODB_IP']}:{os.environ['MONGODB_PORT']}/"
        client = MongoClient(uri)

        db = client['steam']
        collection = db['topgames']

        collection.create_index("appid", unique=False)
        collection.create_index("date", unique=False)

        # pull Steam top 100 games
        # https://store.steampowered.com/charts/mostplayed
        # also see here for historical charting using the same data
        # https://steamcharts.com/

        r = requests.get(
            "https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/",
            params={"key": os.environ["STEAM_API_KEY"]},
            timeout=30
        )
        if (r.ok):
            data = r.json()

            if (pbar):
                bar = progressbar.ProgressBar(max_value=len(data['response']['ranks'])).start()

            date_now = datetime.datetime.now(datetime.UTC)
            for i,row in enumerate(data['response']['ranks']):
                if (pbar):
                    bar.update(i+1)

                towrite = dict()
                towrite['date'] = date_now

                towrite['game'] = ""
                towrite['link'] = ""
                towrite['appid'] = str(row['appid'])

                towrite['currentplayers'] = row['concurrent_in_game']
                towrite['peaktoday'] = row['peak_in_game']

                collection.insert_one(towrite)
            if (pbar):
                bar.finish()
            logging.info("Finished downloading top games.")
            logging.info("Downloaded: " + common.sizeof_fmt(len(r.content)))
            common.writeBandwidth(db, len(r.content))
        else:
            logging.error("status code: " + str(r.status_code))
    except Exception as e:
        logging.error(str(e))
        time.sleep(1)

if __name__== "__main__":
    steamTopGames(pbar=True)
