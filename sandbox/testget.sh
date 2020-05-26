#! /bin/sh

#wget -O log  https://wakeaboo.herokuapp.com/api/v1/entries/?token=raspi-97846cb04ad59b51

wget -q -O -  https://glucalarm.herokuapp.com/api/v1/entries/current/?token=raspi-97846cb04ad59b51 | head -n 1
