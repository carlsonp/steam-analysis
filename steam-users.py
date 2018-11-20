import json, sys, time, requests, datetime, logging
from pymongo import MongoClient, UpdateOne
import progressbar # https://github.com/WoLpH/python-progressbar
import config
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
					filename='steam-analysis.log', level=logging.DEBUG)
# set the logging level for the requests library
logging.getLogger('urllib3').setLevel(logging.WARNING)

client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)
db = client['steam']
collection = db['steamusers']

collection.create_index("epochint", unique=True)

# pull Steam online users
# https://store.steampowered.com/stats/

r = requests.get("https://store.steampowered.com/stats/userdata.json")
data = r.json()[0]['data']

bar = progressbar.ProgressBar(max_value=len(data)).start()

for i,users in enumerate(data):
    bar.update(i+1)
    # convert Epoch to local time
    # https://stackoverflow.com/questions/1697815/how-do-you-convert-a-python-time-struct-time-object-into-a-datetime-object
    conv_time = datetime.datetime.fromtimestamp(time.mktime(time.localtime(int(users[0])/1000)))
    #update_one will keep whatever information already exists
    collection.update_one({'epochint': int(users[0])}, {'$set': {'numberonlineusers': int(users[1]), 'date': conv_time}}, upsert=True)
bar.finish()
