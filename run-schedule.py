import schedule, time, logging

import steamtopgames, steamusers, updatepricehistory, refreshsteam, downloadappids # *.py files

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename='steam-analysis.log', level=logging.DEBUG)

schedule.every(5).minutes.do(steamtopgames.steamTopGames)
schedule.every(23).hours.do(steamusers.steamUsers)
schedule.every(48).hours.do(updatepricehistory.updatePriceHistory)
schedule.every(24).hours.do(refreshsteam.refreshSteamAppIDs, "SAMPLING_GAMES", False)
schedule.every(24).hours.do(refreshsteam.refreshSteamAppIDs, "SAMPLING", False)
schedule.every(24).hours.do(refreshsteam.refreshSteamAppIDs, "MISSING", False)
schedule.every(24).hours.do(downloadappids.downloadAllAppIDs)

sec = 0
while True:
    schedule.run_pending()
    if sec % 600 == 0: # every roughly 10 minutes save the scheduling information to the log
        for job in schedule.jobs:
            logging.info(str(job))
        sec = 0
    time.sleep(1) # seconds
    sec = sec + 1