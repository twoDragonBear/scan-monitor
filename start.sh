#!/bin/bash

cd /root/scan-monitor

source /root/miniconda3/bin/activate
conda activate scan-monitor

python monitor-block.py