# Steam Analysis


### Python Libraries

```
pip3 install pymongo progressbar2 requests schedule beautifulsoup4
```

### Mongo Queries

Find all sales

```
db.apps.find({$expr: {$ne: ["$price_overview.initial", "$price_overview.final"] } })
```

Find the number of missing entries

```
db.apps.count({"updated_date": {"$exists": false}})
```

Find counts of apps by type

```
db.apps.aggregate([
    {"$group" : {_id:"$type", count:{$sum:1}}}
])
```

Average Metacritic rating by developer

```
db.apps.aggregate(
    {
        $group:
            {
                _id: "$developers",
                "avgMetacritic": {$avg: "$metacritic.score"},
		"countMetacritic": {$sum: 1}
            }
    },
    {'$match': {'avgMetacritic': {'$ne': null}}}
)
```

Find price history records ordered by the most recent

```
db.pricehistory.find({}).sort({"date":-1})
```

Number of records that we are skipping due to inability to get information

```
db.apps.count({"failureCount":{"$gte":3}})
```

### Links

#### Additional Datasets and APIs:

https://towardsdatascience.com/predicting-hit-video-games-with-ml-1341bd9b86b0

https://opendata.stackexchange.com/questions/3898/video-game-dataset

https://opendata.stackexchange.com/questions/2120/video-game-meta-data-supplement-for-steam-api/2126#2126

https://www.giantbomb.com/api/

https://igdb.github.io/api/


#### Time Series Forecasting:

https://facebook.github.io/prophet/

https://towardsdatascience.com/time-series-analysis-in-python-an-introduction-70d5a5b1d52a

https://mapr.com/blog/deep-learning-tensorflow/

https://www.analyticsvidhya.com/blog/2018/02/time-series-forecasting-methods/

#### Steam API

https://github.com/BrakeValve/dataflow/issues/5

http://steamwebapi.azurewebsites.net/


### Mongo Backup

Backup all Mongo records to an archive.

```
mongodump --archive=./backups/steam-`date +"%m-%d-%y"`.archive --db steam
```

### Mongo Restore

Restore all Mongo records from an archive.

```
mongorestore -h 127.0.0.1:27017 --drop -vvvvvv -d steam --archive=/home/carlsonp/src/steam-analysis/backups/steam-12-16-18.archive
```

### Spark

Start master node

```
~/spark-2.3.1-bin-hadoop2.7/sbin$ ./start-master.sh --host 192.168.1.171
```

Start work node

```
~/spark-2.3.1-bin-hadoop2.7/sbin$ ./start-slave.sh 192.168.1.171:7077
```

### Mongo

Grab Mongo from Docker
```
docker pull mongo
```

Start Mongo via Docker and bind the port to be accessible via networking
```
docker run -p 27017:27017 --name mongo -d mongo:latest
```

### Raspberry Pi

https://wiki.debian.org/RaspberryPi3

https://github.com/Debian/raspi3-image-spec

https://hub.docker.com/_/mongo/

Flash image with Etcher:

https://www.balena.io/etcher/

### Running via scheduler

```
python3 run-schedule.py
```

Run in the background
```
python3 run-schedule.py &
```

Check the status of the background task
```
top -p `pgrep "python3"`
```

Continue refreshing display of the log file
```
less +F steam-analysis.log
```