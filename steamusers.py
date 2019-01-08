import json, sys, time, re, string, requests, datetime, logging
from pymongo import MongoClient, UpdateOne
from bs4 import BeautifulSoup
import progressbar # https://github.com/WoLpH/python-progressbar
import config # config.py

def steamUsers(pbar=False):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
					filename='steam-analysis.log', level=logging.DEBUG)
    # set the logging level for the requests library
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.info("Running Steam Users Online")

    client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)

    db = client['steam']
    collection = db['steamusers']

    collection.create_index("epochint", unique=True)
    collection.create_index("date", unique=True)

    # pull Steam online users over the last 24 hours
    # https://store.steampowered.com/stats/

    try:
        r = requests.get("https://store.steampowered.com/stats/userdata.json")
        if (r.ok):
            data = r.json()[0]['data']

            if (pbar):
                bar = progressbar.ProgressBar(max_value=len(data)).start()

            for i,users in enumerate(data):
                if (pbar):
                    bar.update(i+1)
                # convert Epoch to local time
                # https://stackoverflow.com/questions/1697815/how-do-you-convert-a-python-time-struct-time-object-into-a-datetime-object
                conv_time = datetime.datetime.fromtimestamp(time.mktime(time.localtime(int(users[0])/1000)))
                #update_one will keep whatever information already exists
                collection.update_one({'epochint': int(users[0])}, {'$set': {'numberonlineusers': int(users[1]), 'date': conv_time}}, upsert=True)
            if (pbar):
                bar.finish()
            logging.info("Finished downloading Steam users online.")
        else:
            logging.error("status code: " + str(r.status_code))
    except Exception as e:
        logging.error(str(e))


if __name__== "__main__":
    steamUsers(pbar=True)