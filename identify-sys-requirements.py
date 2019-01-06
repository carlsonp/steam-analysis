import sys, time, datetime, re, string, logging
from pymongo import MongoClient
import progressbar # https://github.com/WoLpH/python-progressbar
import config
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
					filename='system-requirements.log', level=logging.DEBUG)


client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)
db = client['steam']
collection_apps = db['apps']
collection_reqs = db['systemreqs']

# create an index for appid, this vastly improves performance
collection_reqs.create_index("appid", unique=True)
collection_reqs.create_index("last_updated")

ret = collection_apps.find({}, {"appid":1, "name": 1, "pc_requirements":1,
                            "mac_requirements":1, "linux_requirements":1})

bar = progressbar.ProgressBar(max_value=ret.count()).start()


def findCPUMHZ(s):
    matchGHZ = re.findall( r'(\d+\.\d+)\s*ghz', s, re.I) #re.I = case-insensitive search
    if (len(matchGHZ) == 1):
        return(float(matchGHZ[0])*1000)
    elif (len(matchGHZ) > 1):
        logging.warning("Found multiple GHZ matches: " + s)

    matchMHZ = re.findall( r'(\d+)\s*mhz', s, re.I) #re.I = case-insensitive search
    if (len(matchMHZ) == 1):
        return(int(matchMHZ[0]))
    elif (len(matchMHZ) > 1):
        logging.warning("Found multiple MHZ matches: " + s)

    return None

try:
    for i,app in enumerate(ret):
        bar.update(i+1)
        to_write = {}
        to_write["last_updated"] = datetime.datetime.utcnow()
        to_write["appid"] = app['appid']
        to_write["name"] = app['name']
        for os in ["pc_requirements", "mac_requirements", "linux_requirements"]:
            if (app[os]):
                to_write[os] = {}
                to_write[os + "_orig"] = app[os]
                for req in ['minimum', 'recommended']:
                    if (req in app[os]):
                        html_cleaned = re.compile(r'<[^<]+?>').sub('', app[os][req])
                        #re.I = case-insensitive search
                        #re.S = Make the '.' special character match any character at all, including a newline
                        s = re.search(r'minimum(.*)recommended(.*)', html_cleaned, re.I|re.S)
                        if s:
                            to_write[os]['minimum_cpu_mhz'] = findCPUMHZ(s.group(1))
                            to_write[os]['recommended_cpu_mhz'] = findCPUMHZ(s.group(2))
                        else:
                            to_write[os][req + '_cpu_mhz'] = findCPUMHZ(html_cleaned)

            #print(to_write)
            #sys.exit()


        collection_reqs.replace_one({'appid': app['appid']}, to_write, upsert=True)

    bar.finish()
except Exception as e:
    logging.error(e)
