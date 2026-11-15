#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
if [[ ! -f .env ]]; then
    cp .env.example .env
fi
mkdir -p .ssh
if [[ ! -f .ssh/id_ed25519 ]]; then
    ssh-keygen -q -t ed25519 -N '' -C devops-lab3 -f .ssh/id_ed25519
fi
if [[ ! -f .ssh/id_ed25519.pub ]]; then
    ssh-keygen -y -f .ssh/id_ed25519 > .ssh/id_ed25519.pub
fi
chmod 700 .ssh
chmod 600 .env .ssh/id_ed25519
echo 'Prepared .env and SSH key. Existing files were preserved.'
