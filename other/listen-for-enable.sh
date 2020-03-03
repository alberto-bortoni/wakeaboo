#! /bin/sh

### BEGIN INIT INFO
# Provides:          listen-for-enable.py
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
### END INIT INFO

# If you want a command to always run, put it here

# Carry out specific functions when asked to by the system
case "$1" in
  start)
    echo "Starting listen-for-enable.py"
    /home/boo/wakeaboo/listen-for-enable.py &
    ;;
  stop)
    echo "Stopping listen-for-enable.py"
    pkill -f /home/boo/wakeabo/listen-for-enable.py
    ;;
  restart)
    echo "restarting listen-for-enable.py"
    pkill -f /home/boo/wakeaboo/listen-for-enable.py
    /home/boo/wakeaboo/listen-for-enable.py &
    ;;
  *)
    echo "Usage: /etc/init.d/listen-for-enable.sh {start|stop|restart}"
    exit 1
    ;;
esac

exit 0
