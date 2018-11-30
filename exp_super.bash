#!/bin/bash
python3 super4_miraisim.py --config-json ./tests/config-multiple.json
sleep 3s
rm -f test-average_02.log.txt
