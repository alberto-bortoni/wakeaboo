#!/bin/bash

#Start screen and attach application
NL=`echo -ne '\015'`

#enable and shutdown script
screen -dmS glucApp -t Enshd
screen -S glucApp -p Enshd -X stuff "cd ~/glucalarm/$NL"
screen -S glucApp -X screen -t app
screen -S glucApp -p app -X stuff "cd ~/glucalarm/$NL"
screen -S glucApp -X screen -t nav
screen -S glucApp -p nav -X stuff "cd ~/glucalarm/$NL"
screen -S glucApp -p Enshd -X stuff "python3 glucalarmMain.py$NL"

exit 0
