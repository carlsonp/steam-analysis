#!/bin/bash
mongodump --host=mongo:27017 --archive=/backups/steam-`date +"%m-%d-%y"`.archive --db steam
