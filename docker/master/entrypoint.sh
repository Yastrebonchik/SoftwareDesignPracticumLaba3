#!/bin/sh
set -eu
install -d -m 700 /root/.ssh
install -m 600 /keys/id_ed25519 /root/.ssh/id_ed25519
exec "$@"
