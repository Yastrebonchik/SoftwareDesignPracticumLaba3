#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

deadline=$((SECONDS + 180))
while (( SECONDS < deadline )); do
    container_ids=$(docker compose ps --all --quiet)
    if [[ -n "$container_ids" ]]; then
        mapfile -t ids <<< "$container_ids"
        states=$(docker inspect --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' "${ids[@]}")
        all_healthy=true
        while read -r state health; do
            if [[ "$state" != running || "$health" != healthy ]]; then
                all_healthy=false
            fi
        done <<< "$states"
        if [[ ${#ids[@]} -eq 4 && "$all_healthy" == true ]]; then
            echo 'All four containers are healthy.'
            exit 0
        fi
    fi
    sleep 2
done

echo 'Containers did not become healthy within 180 seconds.' >&2
docker compose ps --all >&2
exit 1
