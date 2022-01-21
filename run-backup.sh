#!/bin/bash
#mongodump --archive=./backups/steam-`date +"%m-%d-%y"`.archive --db steam
rsync -av --delete /home/carlsonp/src/steam-analysis/ /backup2/steam-analysis/
