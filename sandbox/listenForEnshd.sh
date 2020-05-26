#!/bin/sh

# If you want a command to always run, put it here
NL=`echo -ne '\015'`

# Carry out specific functions when asked to by the system
case "$1" in
  start)
    echo "Starting listenForEnshd.py"
    python3 /home/boo/glucalarm/listenForEnshd.py
    ;;
  stop)
    echo "Stopping listenForEnshd.py"
    pkill -f /home/boo/glucalarm/listenForEnshd.py
    ;;
  restart)
    echo "Restarting listenForEnshd.py"
    pkill -f /home/boo/glucalarm/listenForEnshd.py
    screen -S glucApp -p Enshd -X stuff "python3 /home/boo/glucalarm/listenForEnshd.py$NL"
    ;;
  *)
    echo "Usage: /home/boo/glucalarm/listenForEnshd.sh {start|stop|restart}"
    exit 1
    ;;
esac

exit 0
