import schedule, time

import steamtopgames, steamusers, updatepricehistory, refreshsteam, downloadappids # *.py files

schedule.every(5).minutes.do(steamtopgames.steamTopGames)
schedule.every(23).hours.do(steamusers.steamUsers)
schedule.every(48).hours.do(updatepricehistory.updatePriceHistory)
schedule.every(24).hours.do(refreshsteam.refreshSteamAppIDs)
schedule.every(24).hours.do(downloadappids.downloadAllAppIDs)

while True:
    schedule.run_pending()
    time.sleep(1) # seconds