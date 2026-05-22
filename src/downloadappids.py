import time
import requests
import os

from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

import progressbar  # https://github.com/WoLpH/python-progressbar

import common as common  # common.py


def downloadAllAppIDs(pbar=False):
    logging = common.setupLogging()

    try:
        logging.info("Downloading All AppIDs")

        uri = (
            f"mongodb://root:{os.environ['MONGODB_ROOT_PASSWORD']}"
            f"@{os.environ['MONGODB_IP']}:{os.environ['MONGODB_PORT']}/"
        )

        client = MongoClient(uri)
        db = client["steam"]
        collection = db["apps"]

        # Create index once
        collection.create_index("appid", unique=True)

        api_key = os.environ["STEAM_API_KEY"]

        max_results = 10000
        last_appid = 0
        total_downloaded = 0
        total_bandwidth = 0

        bar = None
        if pbar:
            # Unknown total size, so use UnknownLength
            bar = progressbar.ProgressBar(
                max_value=progressbar.UnknownLength
            ).start()

        while True:
            params = {
                "key": api_key,
                "max_results": max_results,
            }

            # Don't send last_appid on first request
            if last_appid > 0:
                params["last_appid"] = last_appid

            r = requests.get("https://api.steampowered.com/IStoreService/GetAppList/v1/", params=params, timeout=30)

            if not r.ok:
                logging.error(f"status code: {r.status_code}")
                break

            total_bandwidth += len(r.content)

            data = r.json()["response"]

            apps = data.get("apps", [])

            if not apps:
                logging.info("No more apps returned.")
                break

            requests_list = []

            for app in apps:
                requests_list.append(
                    UpdateOne(
                        {"appid": int(app["appid"])},
                        {"$set": app},
                        upsert=True,
                    )
                )

            try:
                collection.bulk_write(requests_list, ordered=False)
            except BulkWriteError as bwe:
                logging.error(bwe.details)

            total_downloaded += len(apps)

            if pbar:
                bar.update(total_downloaded)

            logging.info(
                f"Downloaded batch: {len(apps)} apps "
                f"(total: {total_downloaded})"
            )

            # Pagination
            last_appid = data.get("last_appid")

            # Steam tells us if more data exists
            if not data.get("have_more_results", False):
                break

            # Be polite to API
            time.sleep(0.2)

        if pbar and bar:
            bar.finish()

        logging.info(f"Finished downloading AppIDs.")
        logging.info(f"Total apps downloaded: {total_downloaded}")
        logging.info(
            "Downloaded bandwidth: "
            + common.sizeof_fmt(total_bandwidth)
        )

        common.writeBandwidth(db, total_bandwidth)

    except Exception as e:
        logging.error(str(e))
        time.sleep(1)


if __name__ == "__main__":
    downloadAllAppIDs(pbar=True)
