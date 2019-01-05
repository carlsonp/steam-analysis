import json, sys, time, re, string, requests, datetime, logging
from pymongo import MongoClient, UpdateOne
from bs4 import BeautifulSoup
import progressbar # https://github.com/WoLpH/python-progressbar
import config # config.py

def steamTopGames(pbar=False):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
					filename='steam-analysis.log', level=logging.DEBUG)
    # set the logging level for the requests library
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.info("Running Steam Top Games")

    client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)

    db = client['steam']
    collection = db['topgames']

    collection.create_index("appid", unique=False)

    # pull Steam top 100 games
    # https://store.steampowered.com/stats/
    # also see here for historical charting using the same data
    # https://steamcharts.com/

    r = requests.get("https://store.steampowered.com/stats/")
    soup = BeautifulSoup(r.text, 'html.parser')
    rows = soup.find_all('tr', class_="player_count_row")

    if (pbar):
        bar = progressbar.ProgressBar(max_value=len(rows)).start()

    try:
        for i,row in enumerate(rows):
            if (pbar):
                bar.update(i+1)

            towrite = dict()
            towrite['date'] = datetime.datetime.utcnow()

            link = row.find_all('a', class_="gameLink")

            towrite['game'] = link[0].text
            towrite['link'] = link[0].get('href')

            appID = re.search( r'\/app\/(\d*)', link[0].get('href'), re.I)
            if appID and appID.group(1):
                towrite['appid'] = appID.group(1)
            else:
                logging.info("No appID found in URL: " + link[0].get('href'))

            online = row.find_all('span', class_="currentServers")
            towrite['currentplayers'] = int(online[0].text.replace(",", ""))
            towrite['peaktoday'] = int(online[1].text.replace(",", ""))

            collection.insert_one(towrite)
        if (pbar):
            bar.finish()
        logging.info("Finished downloading top games.")
    except Exception as e:
        logging.error(str(e))


if __name__== "__main__":
    steamTopGames(pbar=True)