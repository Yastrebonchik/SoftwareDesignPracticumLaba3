#!/bin/sh
set -eu
install -d -m 700 /root/.ssh
install -m 600 /run/authorized_key /root/.ssh/authorized_keys
mkdir -p /run/sshd
ssh-keygen -A
if [ -x /usr/local/bin/lab-start ]; then
    /usr/local/bin/lab-start
fi
exec /usr/sbin/sshd -D -e
