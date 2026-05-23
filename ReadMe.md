# Steam Analysis

Downloads Steam and other videogame data and saves it in a Mongo database.

## Setup

Copy `.env-copy` to `.env` and edit.

## Docker

```shell
docker compose build --pull
docker compose up -d --build
```

## Docker Debugging

```shell
docker exec -it <id> bash
```

## Docker Development

```shell
docker compose -f docker-compose-dev.yml up -d
```

## Docker Teardown

```shell
docker compose down -v
```

## Helm

Lint the YAML

```shell
helm lint chart
```

Generate the output, helpful for debugging

```shell
helm template chart
```

## Python Libraries

```shell
pip3 install pymongo progressbar2 requests schedule beautifulsoup4
```

## Mongo Queries

Find all sales

```mongo
db.apps.find({$expr: {$ne: ["$price_overview.initial", "$price_overview.final"] } })
```

Find the number of missing entries

```mongo
db.apps.count({"updated_date": {"$exists": false}})
```

Find counts of apps by type

```mongo
db.apps.aggregate([
    {"$group" : {_id:"$type", count:{$sum:1}}}
])
```

Average Metacritic rating by developer

```mongo
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

```mongo
db.pricehistory.find({}).sort({"date":-1})
```

Find when the apps collection was most recently updated

```mongo
db.apps.find({}, {"updated_date":1}).sort({"updated_date":-1})
```

## Mongo Backup

Backup all Mongo records to an archive.

```shell
mongodump -h 127.0.0.1:27017 --archive=./backups/steam-`date +"%m-%d-%y"`.archive --db steam
```

[Backup all Mongo records to an archive via a Docker container](https://blog.studiointeract.com/mongodump-and-mongorestore-for-mongodb-in-a-docker-container-8ad0eb747c62) (helpful for Mongo 4.X vs. 3.X since mongodump has issues across major version changes).

```shell
docker run --rm --name=mongobackup --link mongo:mongobackup -v /root/src/steam-analysis/backups/:/backup mongo bash -c 'mongodump --archive=/backup/steam-`date +"%m-%d-%y"`.archive --db steam --host mongo:27017'
```

## Mongo Restore

Restore all Mongo records from an archive.

```shell
mongorestore -h 127.0.0.1:27017 --drop -vvvvvv -d steam --archive=/home/carlsonp/src/steam-analysis/backups/steam-12-16-18.archive
```

```shell
mongorestore \
  -h 192.168.1.11:27017 \
  --drop \
  -vvvvvv \
  -d steam \
  --archive=steam-05-22-26.archive \
  -u root \
  -p secretpassword \
  --authenticationDatabase admin \
  --tlsInsecure
```

## Debugging

Check docker status

```shell
docker ps -a
docker stats
```

Search the log file for errors

```shell
grep ERROR steam-analysis.log
```

## Links

### Additional Datasets and APIs

https://towardsdatascience.com/predicting-hit-video-games-with-ml-1341bd9b86b0

https://opendata.stackexchange.com/questions/3898/video-game-dataset

https://opendata.stackexchange.com/questions/2120/video-game-meta-data-supplement-for-steam-api/2126#2126

https://www.giantbomb.com/api/

https://igdb.github.io/api/

### Time Series Forecasting

https://facebook.github.io/prophet/

https://towardsdatascience.com/time-series-analysis-in-python-an-introduction-70d5a5b1d52a

https://mapr.com/blog/deep-learning-tensorflow/

https://www.analyticsvidhya.com/blog/2018/02/time-series-forecasting-methods/

https://www.oreilly.com/ideas/3-reasons-to-add-deep-learning-to-your-time-series-toolkit

### Steam API

https://github.com/BrakeValve/dataflow/issues/5

http://steamwebapi.azurewebsites.net/
