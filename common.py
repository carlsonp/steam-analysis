import datetime

# https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
def sizeof_fmt(num, suffix='B'):
    # converts bytes to human-friendly string
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


def setupLogging(log, handlers, sys):
    logging = log.getLogger('steam-analysis')
    logging.setLevel(log.INFO)
    # logging is a singleton, make sure we don't duplicate the handlers and spawn additional log messages
    if not logging.handlers:
        logHandler = handlers.TimedRotatingFileHandler('steam-analysis.log', when='midnight', interval=1)
        logHandler.setLevel(log.INFO)
        logHandler.setFormatter(log.Formatter("[%(filename)s line:%(lineno)d] %(asctime)s - %(levelname)s - %(message)s", '%m/%d/%Y %I:%M:%S %p'))
        logHandler.suffix = "%Y-%m-%d.log"
        logging.addHandler(logHandler)

    if 'requests' in sys.modules:
        # set the logging level for the requests library
        log.getLogger('urllib3').setLevel(log.WARNING)

    return logging


def writeBandwidth(db, bytesamount):
    collection = db['bandwidth']
    collection.create_index("date")

    v = {}
    v['date'] = datetime.datetime.utcnow()
    v['bytes'] = bytesamount
    collection.insert_one(v)
