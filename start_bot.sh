#!/bin/bash
source /root/VizokBot/myenv/bin/activate
nohup python3 /root/VizokBot/main.py > /dev/null 2>&1 &
