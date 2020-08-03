import schedule, time, sys
import logging as log
import logging.handlers as handlers
import common # common.py

import steamtopgames, steamusers, steamreviews, updatepricehistory, refreshsteam, downloadappids, opencriticsearch, opencriticgames, twitchtopgames # *.py files

logging = common.setupLogging(log, handlers, sys)

# run a few things right off the bat since they run infrequently
steamusers.steamUsers()
downloadappids.downloadAllAppIDs()

# schedule items to run
schedule.every(15).minutes.do(steamtopgames.steamTopGames)
schedule.every(23).hours.do(steamusers.steamUsers)
schedule.every(1).hours.do(updatepricehistory.updatePriceHistory, "PARTIAL", False)
schedule.every(45).minutes.do(steamreviews.steamReviews)
schedule.every(3).hours.do(refreshsteam.refreshSteamAppIDs, "SAMPLING", False)
schedule.every(6).hours.do(refreshsteam.refreshSteamAppIDs, "MISSING", False)
schedule.every(24).hours.do(downloadappids.downloadAllAppIDs)
schedule.every(1).hours.do(opencriticsearch.updateOpenCritic, "PARTIAL", False)
schedule.every(1).hours.do(opencriticgames.updateOpenCritic, "OLDEST", False)
schedule.every(9).hours.do(twitchtopgames.updateTwitchTopGames, "TOP", False)

sec = 0
while True:
    schedule.run_pending()
    if sec % 7200 == 0: # every roughly 2 hours save the scheduling information to the log
        for job in schedule.jobs:
            logging.info(str(job))
        sec = 0
    time.sleep(1) # seconds
    sec = sec + 1