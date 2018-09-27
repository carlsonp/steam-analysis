# Steam Analysis

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


### Spark

Start master node

```
~/spark-2.3.1-bin-hadoop2.7/sbin$ ./start-master.sh --host 192.168.1.171
```

Start work node

```
~/spark-2.3.1-bin-hadoop2.7/sbin$ ./start-slave.sh 192.168.1.171:7077
```
