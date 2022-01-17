import datetime, socket, sys
import logging
from logging.handlers import TimedRotatingFileHandler

# https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
def sizeof_fmt(num, suffix='B'):
    # converts bytes to human-friendly string
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


def setupLogging():
    l = logging.getLogger(__name__)
    l.setLevel(logging.INFO)
    # logging is a singleton, make sure we don't duplicate the handlers and spawn additional log messages
    if not l.hasHandlers():
        # we're running manually via Python invocation or Docker
        logHandler = TimedRotatingFileHandler('./logs/steam-analysis.log', when='midnight', interval=1)
        logHandler.setLevel(logging.INFO)
        logHandler.setFormatter(logging.Formatter("[%(filename)s line:%(lineno)d] %(asctime)s - %(levelname)s - %(message)s", '%m/%d/%Y %I:%M:%S %p'))
        logHandler.suffix = "%Y-%m-%d.log"
        l.addHandler(logHandler)
        if socket.gethostname() == "steam":
            # we're running via Docker, also log to stdout
            logHandler = logging.StreamHandler(sys.stdout)
            logHandler.setLevel(logging.INFO)
            logHandler.setFormatter(logging.Formatter("[%(filename)s line:%(lineno)d] %(asctime)s - %(levelname)s - %(message)s", '%m/%d/%Y %I:%M:%S %p'))
            l.addHandler(logHandler)

    if 'requests' in sys.modules:
        # set the logging level for the requests library
        logging.getLogger('urllib3').setLevel(logging.WARNING)

    return l


def writeBandwidth(db, bytesamount):
    collection = db['bandwidth']
    collection.create_index("date")

    v = {}
    v['date'] = datetime.datetime.utcnow()
    v['bytes'] = bytesamount
    collection.insert_one(v)
