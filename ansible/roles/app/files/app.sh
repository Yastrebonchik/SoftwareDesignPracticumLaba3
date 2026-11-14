#!/bin/bash
set -euo pipefail

APP_DIR=/opt/notes
PID_FILE="$APP_DIR/run/app.pid"
LOG_FILE="$APP_DIR/log/app.log"
exec 9>"$APP_DIR/run/control.lock"
flock -x 9

is_running() {
    [[ -f "$PID_FILE" ]] || return 1
    read -r pid < "$PID_FILE"
    [[ "$pid" =~ ^[0-9]+$ ]] || return 1
    kill -0 "$pid" 2>/dev/null || return 1
    [[ -r "/proc/$pid/cmdline" ]] || return 1
    tr '\0' '\n' < "/proc/$pid/cmdline" | grep -Fxq "$APP_DIR/app.jar"
}

start() {
    if is_running; then
        echo "RUNNING $pid"
        return
    fi
    set -a
    source "$APP_DIR/app.env"
    set +a
    nohup java -jar "$APP_DIR/app.jar" >> "$LOG_FILE" 2>&1 < /dev/null 9>&- &
    echo "$!" > "$PID_FILE"
    echo "STARTED $!"
}

stop() {
    if is_running; then
        kill "$pid"
        for ((attempt = 0; attempt < 30; attempt++)); do
            if ! is_running; then
                break
            fi
            sleep 1
        done
        if is_running; then
            kill -KILL "$pid"
        fi
    fi
    rm -f "$PID_FILE"
    echo STOPPED
}

case "${1:-}" in
    start) start ;;
    stop) stop ;;
    restart) stop; start ;;
    status)
        if is_running; then
            echo "RUNNING $pid"
        else
            echo STOPPED
            exit 1
        fi
        ;;
    *) echo "Usage: $0 {start|stop|restart|status}" >&2; exit 2 ;;
esac
