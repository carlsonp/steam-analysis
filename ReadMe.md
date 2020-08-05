# Steam Analysis

[![Total alerts](https://img.shields.io/lgtm/alerts/g/carlsonp/steam-analysis.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/carlsonp/steam-analysis/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/carlsonp/steam-analysis.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/carlsonp/steam-analysis/context:python)

## Setup

Copy `config_example.py` to `config.py` and edit.

## Python Libraries

```shell
pip3 install pymongo progressbar2 requests schedule beautifulsoup4
```

## Bandwidth Monitoring

```
sudo apt-get install vnstat
vnstat
```

## Mongo Queries

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

Find when the apps collection was most recently updated

```
db.apps.find({}, {"updated_date":1}).sort({"updated_date":-1})
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

## Spark

Start master node

```shell
~/spark-2.3.1-bin-hadoop2.7/sbin$ ./start-master.sh --host 192.168.1.171
```

Start work node

```shell
~/spark-2.3.1-bin-hadoop2.7/sbin$ ./start-slave.sh 192.168.1.171:7077
```

## Mongo

Use Mongo 4.X+

Grab Mongo from Docker

```shell
docker pull mongo
```

Start Mongo via Docker and bind the port to be accessible via networking
in addition to setting up a replicaset.

```shell
docker run -p 27017:27017 --name mongo -d mongo:latest --replSet "rs0" --bind_ip 127.0.0.1,192.168.1.224
```

Connect to Mongo (the Master) and add the Master and Slave nodes to the configuration

```
rs.initiate()
rs.add( { host: "192.168.1.224:27017", priority: 1, votes: 1 } )
rs.add( { host: "192.168.1.124:27017", priority: 0, votes: 0 } )
```

Check the status

```
rs.status()
```

## Raspberry Pi

https://wiki.debian.org/RaspberryPi3

https://github.com/Debian/raspi3-image-spec

https://hub.docker.com/_/mongo/

Flash image with Etcher:

https://www.balena.io/etcher/

## Running via scheduler

Run normally

```shell
python3 run-schedule.py
```

Run in the background

```shell
python3 run-schedule.py &
```

Check the status of the background task

```shell
top -p `pgrep "python3"`
```

Continue refreshing display of the log file

```shell
less +F steam-analysis.log
```

Check bandwidth usage

```shell
ip -stats -color -human addr
```

Check docker status

```shell
docker ps -a
docker stats
```

## Systemd

Using systemd to automatically start Mongo in Docker as well as the Python scheduler
on the Raspberry Pi 3.
These will automatically restart if they're killed off or fail.  They will also
launch on startup.

Create a service for Mongo by creating a new file (contents below).

```shell
$ cat /etc/systemd/system/mongodocker.service 
[Unit]
Description=Mongo via Docker
After=network.target
StartLimitIntervalSec=0
Requires=docker.service
Wants=network-online.target docker.socket

[Service]
Restart=always
RestartSec=2
User=root
ExecStart=docker start -a mongo
ExecStop=docker stop mongo

[Install]
WantedBy=multi-user.target
```

Create a service for the Python scheduler by creating a new file (contents below).
The pre sleep ensures Mongo is up and running before we start.

```shell
$ cat /etc/systemd/system/steamanalysis.service 
[Unit]
Description=Steam analysis
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=root
ExecStartPre=/bin/sleep 50
ExecStart=python3 -u /root/src/steam-analysis/run-schedule.py &
WorkingDirectory=/root/src/steam-analysis/

[Install]
WantedBy=multi-user.target
```

Enable the services which will start it each boot.  This will create the appropriate symlinks.

```shell
systemctl enable mongodocker
systemctl enable steamanalysis
```

Start the services

```shell
systemctl start mongodocker
systemctl start steamanalysis
```

Check the status of each service

```shell
systemctl status mongodocker.service
systemctl status steamanalysis.service
```

Check the log files of the services via systemd

```shell
journalctl -u mongodocker.service
journalctl -u steamanalysis.service
```

Search the log file for errors

```shell
grep ERROR steam-analysis.log
```
