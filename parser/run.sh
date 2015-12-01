#/bin/bash
while ./parse.py; do
    echo "Parser stopped.  Respawning.." >&2
    sleep 1
done
